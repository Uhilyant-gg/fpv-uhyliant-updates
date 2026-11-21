"""Pure post-operation verification helpers. Hardware acquisition stays outside this module."""
from openipc_device import normalize_openipc_identity

def verify_post_flash(before, observed, profile, expected_firmware=""):
    current=normalize_openipc_identity(observed, observed.get("evidence",[]) if isinstance(observed,dict) else [])
    checks=[]
    def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
    add("rediscovered",bool(observed),"Device rediscovered" if observed else "Device not rediscovered")
    add("openipc",current.get("verified"),"OpenIPC evidence verified" if current.get("verified") else "OpenIPC evidence unavailable")
    add("hardware",current.get("platform","").lower()==profile.get("platform","").lower() and current.get("sensor","").lower()==profile.get("sensor","").lower(),"Platform/sensor match" if current.get("platform","").lower()==profile.get("platform","").lower() and current.get("sensor","").lower()==profile.get("sensor","").lower() else "Platform/sensor mismatch")
    fw_ok=not expected_firmware or current.get("firmware")==expected_firmware;add("firmware",fw_ok,"Observed firmware matches expected" if fw_ok else "Observed firmware does not match expected")
    same_identity=not before or (current.get("platform")==before.get("platform") and current.get("sensor")==before.get("sensor"));add("identity-continuity",same_identity,"Hardware identity preserved" if same_identity else "Hardware identity changed")
    return {"ok":all(c["ok"] for c in checks),"checks":checks,"identity":current}
