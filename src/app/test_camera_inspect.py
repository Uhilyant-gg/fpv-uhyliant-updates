import camera_inspect as ci
import camera_setup as cs

ZT_INFO = "200 info 89e92ceee5 1.12.2 ONLINE\n"
ZT_NETWORKS = (
    "200 listnetworks <nwid> <name> <mac> <status> <type> <dev> <ZT assigned ips>\n"
    "200 listnetworks 8056c2e21c000001 drone 0a:1b:2c:3d:4e:5f OK PRIVATE ztabcdef fd80:56c2:e21c:0:199:9389:e92c:eee5/88\n"
)
IPV6 = (
    "2: eth0    inet6 2a0d:3344:1:2::10/64 scope global dynamic \\    valid_lft 86000sec\n"
    "3: ztabcdef    inet6 fd80:56c2:e21c:0:199:9389:e92c:eee5/88 scope global \\    valid_lft forever\n"
)
RELEASE = 'NAME="OpenIPC"\nVERSION_ID="2.5"\nOPENIPC_VERSION="2.5.06.12"\nBUILD_OPTION="fpv"\n'
MTD = (
    "dev:    size   erasesize  name\n"
    'mtd0: 00040000 00010000 "boot"\nmtd1: 00010000 00010000 "env"\n'
    'mtd2: 00200000 00010000 "kernel"\nmtd3: 00500000 00010000 "rootfs"\nmtd4: 00870000 00010000 "rootfs_data"\n'
)
DF = "Filesystem           1K-blocks      Used Available Use% Mounted on\n/dev/mtdblock4            8640      1520      7120  18% /overlay\n"


class Session:
    def __init__(self, answers):
        self.answers = answers
        self.commands = []

    def run(self, command):
        self.commands.append(command)
        return (0, self.answers[command]) if command in self.answers else (127, "")


def full():
    return {
        "zerotier-cli info": ZT_INFO,
        "zerotier-cli listnetworks": ZT_NETWORKS,
        "ip -6 -o addr show scope global": IPV6,
        "cat /etc/os-release": RELEASE,
        "cat /proc/mtd": MTD,
        "df -k /overlay": DF,
    }


def test_reads_every_fact():
    session = Session(full())
    facts = ci.read_facts(session)
    assert facts == {
        "ztInstalled": True,
        "ztNode": "89e92ceee5",
        "ztNetwork": "8056c2e21c000001",
        "ipv6": ["2a0d:3344:1:2::10"],
        "flashMb": 16,
        "freeKb": 7120,
        "firmware": "OpenIPC",
        "variant": "fpv",
        "version": "2.5.06.12",
    }
    assert set(session.commands) == set(ci.READ_ONLY_COMMANDS.values()), "only the read-only commands"
    assert ci.summary(facts) == "OpenIPC fpv 2.5.06.12 · флеш 16 МБ · вільно 7,0 МБ · ZeroTier є"
    assert ci.valid_zt(facts) == ("8056c2e21c000001", "89e92ceee5")


def test_camera_without_zerotier_and_unknown_answers():
    session = Session({"cat /proc/mtd": "garbage", "df -k /overlay": "nothing"})
    facts = ci.read_facts(session)
    assert facts["ztInstalled"] is False and facts["ztNode"] == "" and facts["ztNetwork"] == ""
    assert facts["flashMb"] == 0 and facts["freeKb"] == 0 and facts["ipv6"] == []
    assert "zerotier-cli listnetworks" not in session.commands
    assert ci.summary(facts) == "ZeroTier немає"
    assert ci.valid_zt(facts) == ("", "")


def test_several_networks_pick_the_only_one_that_is_up():
    two = ZT_NETWORKS + "200 listnetworks 1111111111111111 old 0a:00:00:00:00:01 ACCESS_DENIED PRIVATE zt2 -\n"
    assert ci.pick_network(ci.parse_zt_networks(two)) == "8056c2e21c000001"
    both_up = two.replace("ACCESS_DENIED", "OK")
    assert ci.pick_network(ci.parse_zt_networks(both_up)) == "", "ambiguous: nothing is guessed"


def test_link_local_and_private_ipv6_are_ignored():
    text = "inet6 fe80::1/64 scope link\ninet6 fd00::5/64 scope global\ninet6 2001:4860::1/64 scope global\n"
    assert ci.parse_global_ipv6(text) == ["2001:4860::1"]


def test_inspect_uses_the_shared_login():
    camera = Session(full())

    class Shell:
        def __init__(self, host, user, password):
            self.password = password

        def __enter__(self):
            if self.password != "12345":
                raise cs.SetupError("no-access")
            return camera

        def __exit__(self, *exc):
            return False

    result = ci.inspect_camera("192.168.1.10", [("root", "wrong"), ("root", "12345")], Shell)
    assert result["state"] == "read" and result["ztNode"] == "89e92ceee5"
    assert ci.inspect_camera("192.168.1.10", [("root", "wrong")], Shell)["state"] == "no-access"


def test_shell_accepts_zerotier_addresses(tmp_path):
    class Client:
        def connect(self, host, **kwargs):
            self.host = host

        def close(self):
            pass

    with cs.CameraShell(
        "fd80:56c2:e21c:0:199:9389:e92c:eee5", "root", "12345", tmp_path / "k", client_factory=Client
    ) as s:
        assert s.client.host.startswith("fd80:")


class CountingShell:
    """A camera that counts logins and can drop the connection."""

    def __init__(self):
        self.logins = 0
        self.closed = 0
        self.broken = False
        self.password = "12345"

    def __call__(self, host, user, password):
        camera = self

        class Shell:
            def __enter__(self):
                if password != camera.password:
                    raise cs.SetupError("no-access")
                camera.logins += 1
                return self

            def __exit__(self, *exc):
                camera.closed += 1
                return False

            def run(self, command):
                if camera.broken:
                    raise OSError("connection lost")
                return Session(full()).run(command)

        return Shell()


def test_pool_logs_in_once_and_reuses_the_session():
    camera = CountingShell()
    pool = ci.InspectorPool(lambda: [("root", "12345")], camera)
    for _ in range(5):
        assert pool.inspect("192.168.1.10")["ztNode"] == "89e92ceee5"
    assert camera.logins == 1, "one login for many reads"
    assert pool.open_sessions == 1


def test_pool_logs_in_again_after_the_connection_drops():
    camera = CountingShell()
    pool = ci.InspectorPool(lambda: [("root", "12345")], camera)
    pool.inspect("192.168.1.10")
    camera.broken = True
    assert pool.inspect("192.168.1.10")["state"] == "failed"
    assert camera.closed >= 1 and pool.open_sessions == 0
    camera.broken = False
    assert pool.inspect("192.168.1.10")["state"] == "read"
    assert camera.logins == 3, "first login, one immediate re-login when the link dropped, then a new session"


def test_pool_close_all_before_a_flight():
    camera = CountingShell()
    pool = ci.InspectorPool(lambda: [("root", "12345")], camera)
    pool.inspect("192.168.1.10")
    pool.inspect("192.168.1.11")
    pool.close_all()
    assert pool.open_sessions == 0 and camera.closed == 2


def test_pool_reports_a_wrong_password():
    camera = CountingShell()
    camera.password = "other"
    pool = ci.InspectorPool(lambda: [("root", "a"), ("root", "12345")], camera)
    assert pool.inspect("192.168.1.10")["state"] == "no-access"
    assert pool.open_sessions == 0
