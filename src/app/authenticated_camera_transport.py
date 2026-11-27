"""Password-capable SSH transport with no secret in argv, logs, status or errors."""

import ipaddress
from openipc_upgrade import UPGRADE_ARGV


class AuthenticatedCameraTransport:
    def __init__(self, credentials, client_factory=None, timeout=20):
        self.credentials = credentials
        self.client_factory = client_factory
        self.timeout = max(5, min(int(timeout), 120))

    def _address(self, host):
        try:
            a = ipaddress.ip_address(str(host).strip())
        except ValueError:
            return None
        return a if a.version == 4 and not (a.is_unspecified or a.is_multicast or a.is_loopback) else None

    def _client(self):
        if self.client_factory:
            return self.client_factory()
        import paramiko

        c = paramiko.SSHClient()
        c.load_system_host_keys()
        c.set_missing_host_key_policy(paramiko.RejectPolicy())
        return c

    def _connect(self, host):
        address = self._address(host)
        username = self.credentials.username
        password = self.credentials.secret()
        if address is None or not username or not password:
            return None
        client = self._client()
        try:
            client.connect(
                str(address),
                username=username,
                password=password,
                timeout=self.timeout,
                auth_timeout=self.timeout,
                banner_timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            return client
        except Exception:
            try:
                client.close()
            except Exception:
                pass
            return None

    def authenticate(self, host):
        client = self._connect(host)
        if client is None:
            return False
        try:
            return True
        finally:
            client.close()

    def run(self, host, argv):
        if tuple(argv) != UPGRADE_ARGV:
            return False
        client = self._connect(host)
        if client is None:
            return False
        try:
            _stdin, stdout, _stderr = client.exec_command('sysupgrade -k -r', timeout=self.timeout)
            return stdout.channel.recv_exit_status() == 0
        except Exception:
            return False
        finally:
            client.close()
