"""OpenSSH transport using OS-configured authentication and strict host trust."""
import ipaddress
import subprocess
ALLOWED_ARGV=("sysupgrade","-k","-r")
class ExistingSshTransport:
 def __init__(self,runner=subprocess.run,timeout=20):self.runner=runner;self.timeout=max(5,min(int(timeout),120))
 def _host(self,host):
  try:a=ipaddress.ip_address(str(host).strip())
  except ValueError:return None
  return a if a.version==4 and not (a.is_unspecified or a.is_multicast or a.is_loopback) else None
 def _call(self,address,remote):
  command=["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=5",f"root@{address}",*remote]
  try:return self.runner(command,capture_output=True,text=True,timeout=self.timeout).returncode==0
  except (OSError,subprocess.SubprocessError):return False
 def authenticate(self,host):
  address=self._host(host);return bool(address and self._call(address,["true"]))
 def run(self,host,argv):
  address=self._host(host)
  if address is None or tuple(argv)!=ALLOWED_ARGV:return False
  return self._call(address,list(ALLOWED_ARGV))
