"""OpenSSH transport using an existing user SSH configuration.

No password, private key, token or host-key bypass is accepted by this module.
Authentication and host trust must already be configured outside the app.
"""
import ipaddress
import subprocess

ALLOWED_ARGV=("sysupgrade","-k","-r")

class ExistingSshTransport:
 def __init__(self,runner=subprocess.run,timeout=20):self.runner=runner;self.timeout=max(5,min(int(timeout),120))
 def run(self,host,argv):
  try:
   address=ipaddress.ip_address(str(host).strip())
  except ValueError:return False
  if address.version!=4 or address.is_unspecified or address.is_multicast or address.is_loopback:return False
  if tuple(argv)!=ALLOWED_ARGV:return False
  command=["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=5",f"root@{address}",*ALLOWED_ARGV]
  try:return self.runner(command,capture_output=True,text=True,timeout=self.timeout).returncode==0
  except (OSError,subprocess.SubprocessError):return False
