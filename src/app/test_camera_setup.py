import pytest

import camera_setup as cs


class FakeCamera:
    def __init__(self, password="12345", codec="h265", server="udp://127.0.0.1:5600", enabled="false", fail=None):
        self.password, self.codec, self.config = password, codec, {"server": server, "enabled": enabled}
        self.fail = fail
        self.commands = []
        self.logins = []

    def shell(self, host, username, password):
        camera = self

        class Session:
            def __enter__(self):
                camera.logins.append((host, username, password))
                if camera.fail:
                    raise cs.SetupError(camera.fail)
                if password != camera.password:
                    raise cs.SetupError("no-access")
                return self

            def __exit__(self, *exc):
                return False

            def run(self, command):
                camera.commands.append(command)
                if command == "cli -g .video0.codec":
                    return 0, camera.codec
                if command == "cli -g .outgoing.server":
                    return 0, camera.config["server"]
                if command == "cli -g .outgoing.enabled":
                    return 0, camera.config["enabled"]
                if command.startswith("cli -s .outgoing.server "):
                    camera.config["server"] = command.split()[-1]
                    return 0, ""
                if command == "cli -s .outgoing.enabled true":
                    camera.config["enabled"] = "true"
                    return 0, ""
                if command == "killall -1 majestic":
                    return 0, ""
                return 127, ""

        return Session()


def test_configures_the_outgoing_stream_with_the_factory_password():
    camera = FakeCamera()
    result = cs.configure_push(
        "192.168.1.10", "93.170.12.5", 5602, [("root", "")] + list(cs.DEFAULT_CREDENTIALS), camera.shell
    )
    assert result["state"] == "configured" and result["codec"] == "h265"
    assert camera.config == {"server": "udp://93.170.12.5:5602", "enabled": "true"}
    assert camera.commands[-1] == "killall -1 majestic"
    assert camera.logins == [("192.168.1.10", "root", "12345")], "an empty session password is skipped"


def test_session_password_is_tried_first():
    camera = FakeCamera(password="secret")
    result = cs.configure_push(
        "192.168.1.10", "93.170.12.5", 5600, [("root", "secret"), ("root", "12345")], camera.shell
    )
    assert result["state"] == "configured"
    assert len(camera.logins) == 1


def test_nothing_is_changed_when_already_configured():
    camera = FakeCamera(server="udp://93.170.12.5:5600", enabled="true", codec="H264")
    result = cs.configure_push("192.168.1.10", "93.170.12.5", 5600, cs.DEFAULT_CREDENTIALS, camera.shell)
    assert result["state"] == "already" and result["codec"] == "h264"
    assert not any(c.startswith("cli -s") or c.startswith("killall") for c in camera.commands)


def test_wrong_passwords_ask_for_the_camera_password():
    camera = FakeCamera(password="other")
    result = cs.configure_push("192.168.1.10", "93.170.12.5", 5600, [("root", "a"), ("root", "12345")], camera.shell)
    assert result["state"] == "no-access"
    assert "пароль" in result["message"]
    assert len(camera.logins) == 2


@pytest.mark.parametrize("state", ["unsafe", "unreachable"])
def test_connection_problems_stop_without_retrying(state):
    camera = FakeCamera(fail=state)
    result = cs.configure_push("192.168.1.10", "93.170.12.5", 5600, [("root", "a"), ("root", "12345")], camera.shell)
    assert result["state"] == state
    assert len(camera.logins) == 1


def test_camera_refusing_the_setting_is_reported():
    camera = FakeCamera()
    original = camera.shell

    def shell(*args):
        session = original(*args)
        run = session.run
        session.run = lambda command: (1, "") if command.startswith("cli -s") else run(command)
        return session

    assert cs.configure_push("192.168.1.10", "93.170.12.5", 5600, cs.DEFAULT_CREDENTIALS, shell)["state"] == "failed"


@pytest.mark.parametrize(
    "address,port",
    [("93.170.12.5; reboot", 5600), ("$(reboot)", 5600), ("93.170.12.5", 80), ("93.170.12.5", 70000), ("", 5600)],
)
def test_only_validated_values_reach_the_camera(address, port):
    camera = FakeCamera()
    assert cs.configure_push("192.168.1.10", address, port, cs.DEFAULT_CREDENTIALS, camera.shell)["state"] == "failed"
    assert camera.commands == [] and camera.logins == []


def test_setup_commands_reject_anything_but_a_plain_target():
    assert (
        cs.setup_commands("udp://drone.example.net:5600")[1] == "cli -s .outgoing.server udp://drone.example.net:5600"
    )
    with pytest.raises(ValueError):
        cs.setup_commands("udp://x:5600;reboot")


def test_shell_refuses_public_addresses(tmp_path):
    shell = cs.CameraShell("93.170.12.5", "root", "12345", tmp_path / "known", client_factory=object)
    with pytest.raises(cs.SetupError) as error:
        shell.__enter__()
    assert error.value.state == "unreachable"


@pytest.mark.parametrize(
    "error,state",
    [("AuthenticationException", "no-access"), ("BadHostKeyException", "unsafe"), ("socket", "unreachable")],
)
def test_shell_maps_ssh_errors(tmp_path, error, state):
    import socket

    import paramiko

    def raise_error():
        if error == "AuthenticationException":
            raise paramiko.AuthenticationException("bad password")
        if error == "BadHostKeyException":
            key = paramiko.RSAKey.generate(1024)
            raise paramiko.BadHostKeyException("192.168.1.10", key, key)
        raise socket.timeout("timed out")

    class Client:
        closed = False

        def connect(self, *args, **kwargs):
            raise_error()

        def close(self):
            Client.closed = True

    shell = cs.CameraShell("192.168.1.10", "root", "12345", tmp_path / "known", client_factory=Client)
    with pytest.raises(cs.SetupError) as raised:
        shell.__enter__()
    assert raised.value.state == state
    assert Client.closed
