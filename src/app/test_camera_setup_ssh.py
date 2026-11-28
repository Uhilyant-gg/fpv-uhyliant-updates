"""Real SSH (paramiko client and server): login, host-key memory and the camera commands."""

import socket
import threading

import paramiko
import pytest

import camera_setup as cs


class FakeCameraServer(paramiko.ServerInterface):
    def __init__(self, camera):
        self.camera = camera
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        self.camera["logins"] = self.camera.get("logins", 0) + 1
        ok = username == "root" and password == self.camera["password"]
        return paramiko.AUTH_SUCCESSFUL if ok else paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED if kind == "session" else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, command):
        command = command.decode()
        self.camera["commands"].append(command)
        config = self.camera["config"]
        output, code = "", 0
        if command == "cli -g .video0.codec":
            output = "h265"
        elif command.startswith("cli -g .outgoing."):
            output = config.get(command.split(".")[-1], "")
        elif command.startswith("cli -s .outgoing."):
            _, _, key, value = command.split(" ", 3)
            config[key.split(".")[-1]] = value
        elif command in self.camera.get("answers", {}):
            output = self.camera["answers"][command]
        elif command != "killall -1 majestic":
            code = 127

        def reply():
            # like a real sshd: acknowledge the exec request first, then answer
            channel.send(output.encode())
            channel.send_exit_status(code)
            channel.close()

        threading.Timer(0.02, reply).start()
        return True


def serve(camera, host_key):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)

    def loop():
        while True:
            try:
                connection, _ = listener.accept()
            except OSError:
                return
            transport = paramiko.Transport(connection)
            transport.add_server_key(host_key)
            try:
                transport.start_server(server=FakeCameraServer(camera))
            except Exception:
                continue

    threading.Thread(target=loop, daemon=True).start()
    return listener


@pytest.fixture
def camera():
    data = {"password": "12345", "config": {"server": "udp://127.0.0.1:5600", "enabled": "false"}, "commands": []}
    key = paramiko.RSAKey.generate(2048)
    listener = serve(data, key)
    data["port"] = listener.getsockname()[1]
    data["listener"] = listener
    yield data
    listener.close()


def shell_for(camera, known):
    return lambda host, user, password: cs.CameraShell(host, user, password, known, port=camera["port"], timeout=5)


def test_real_ssh_configures_the_camera_and_remembers_its_key(camera, tmp_path):
    known = tmp_path / "camera_known_hosts"
    result = cs.configure_push("127.0.0.1", "93.170.12.5", 5602, cs.DEFAULT_CREDENTIALS, shell_for(camera, known))
    assert result["state"] == "configured", result
    assert result["codec"] == "h265"
    assert camera["config"] == {"server": "udp://93.170.12.5:5602", "enabled": "true"}
    assert "killall -1 majestic" in camera["commands"]
    assert known.exists() and known.read_text().strip(), "the camera's key is remembered"

    again = cs.configure_push("127.0.0.1", "93.170.12.5", 5602, cs.DEFAULT_CREDENTIALS, shell_for(camera, known))
    assert again["state"] == "already"


def test_real_ssh_wrong_password(camera, tmp_path):
    camera["password"] = "changed"
    result = cs.configure_push(
        "127.0.0.1", "93.170.12.5", 5600, cs.DEFAULT_CREDENTIALS, shell_for(camera, tmp_path / "known")
    )
    assert result["state"] == "no-access"
    assert camera["config"]["enabled"] == "false"


def test_real_ssh_refuses_a_camera_whose_key_changed(camera, tmp_path):
    known = tmp_path / "known"
    assert (
        cs.configure_push("127.0.0.1", "93.170.12.5", 5600, cs.DEFAULT_CREDENTIALS, shell_for(camera, known))["state"]
        == "configured"
    )
    impostor = {"password": "12345", "config": {"server": "", "enabled": "false"}, "commands": []}
    other = serve(impostor, paramiko.RSAKey.generate(2048))
    try:
        # same host and port as remembered, different key
        camera["listener"].close()
        known.write_text(
            known.read_text().replace(f"[127.0.0.1]:{camera['port']}", f"[127.0.0.1]:{other.getsockname()[1]}")
        )
        impostor["port"] = other.getsockname()[1]
        result = cs.configure_push("127.0.0.1", "93.170.12.5", 5600, cs.DEFAULT_CREDENTIALS, shell_for(impostor, known))
    finally:
        other.close()
    assert result["state"] == "unsafe"
    assert impostor["commands"] == [], "nothing is sent to an unknown device"


def test_real_ssh_reads_the_camera_ids(camera, tmp_path):
    import camera_inspect as ci

    camera["answers"] = {
        "zerotier-cli info": "200 info 89e92ceee5 1.12.2 ONLINE",
        "zerotier-cli listnetworks": "200 listnetworks 8056c2e21c000001 drone 0a:1b:2c:3d:4e:5f OK PRIVATE zt0 -",
        "cat /etc/os-release": 'NAME="OpenIPC"\nBUILD_OPTION="fpv"',
    }
    result = ci.inspect_camera("127.0.0.1", cs.DEFAULT_CREDENTIALS, shell_for(camera, tmp_path / "known"))
    assert result["state"] == "read"
    assert (result["ztNetwork"], result["ztNode"]) == ("8056c2e21c000001", "89e92ceee5")
    assert result["variant"] == "fpv"
    assert not any(c.startswith("cli -s") or c.startswith("killall") for c in camera["commands"]), "read only"


def test_real_ssh_pool_keeps_one_session_for_frequent_reads(camera, tmp_path):
    import camera_inspect as ci

    camera["answers"] = {"zerotier-cli info": "200 info 89e92ceee5 1.12.2 ONLINE"}
    pool = ci.InspectorPool(lambda: list(cs.DEFAULT_CREDENTIALS), shell_for(camera, tmp_path / "known"))
    try:
        for _ in range(4):
            assert pool.inspect("127.0.0.1")["ztNode"] == "89e92ceee5"
    finally:
        pool.close_all()
    assert camera["logins"] == 1, "frequent reads use one SSH login"
