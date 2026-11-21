"""OpenIPC in-place upgrade policy and command construction.

No shell interpolation: only a verified host and fixed sysupgrade argv are accepted.
The transport itself is deliberately an adapter boundary until credentials and
physical target validation are available.
"""
import ipaddress

LATEST_SOURCE="OpenIPC GitHub latest release"
UPGRADE_ARGV=("sysupgrade","-k","-r")

def upgrade_candidate(device):
    identity=dict((device or {}).get("openipcIdentity") or {})
    host=str((device or {}).get("host","")).strip()
    try: address=ipaddress.ip_address(host)
    except ValueError:return {"ready":False,"reason":"Адреса камери не є IPv4","host":"","argv":[]}
    if address.version!=4 or address.is_unspecified or address.is_multicast or address.is_loopback:
        return {"ready":False,"reason":"Адреса камери непридатна для оновлення","host":"","argv":[]}
    if identity.get("verified") is not True:
        return {"ready":False,"reason":"OpenIPC не підтверджено","host":host,"argv":[]}
    platform=str(identity.get("platform","")).strip().lower()
    sensor=str(identity.get("sensor","")).strip().lower()
    if not platform or not sensor:
        return {"ready":False,"reason":"Платформу або сенсор не підтверджено","host":host,"argv":[]}
    return {"ready":True,"reason":"Камера готова до штатного OpenIPC sysupgrade","host":host,"platform":platform,"sensor":sensor,"currentFirmware":str(identity.get("firmware","")).strip(),"source":LATEST_SOURCE,"argv":list(UPGRADE_ARGV)}
