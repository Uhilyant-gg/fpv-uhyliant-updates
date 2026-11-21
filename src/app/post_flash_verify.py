"""Pure post-operation verification helpers. Hardware acquisition stays outside this module."""
from openipc_device import normalize_openipc_identity

def verify_post_flash(before, observed, profile, expected_firmware=""):
    current=normalize_openipc_identity(observed, observed.get("evidence",[]) if isinstance(observed,dict) else [])
    checks=[]
    def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
    add("rediscovered",bool(observed),"Пристрій повторно виявлено" if observed else "Пристрій не виявлено повторно")
    add("openipc",current.get("verified"),"Докази OpenIPC підтверджено" if current.get("verified") else "Докази OpenIPC недоступні")
    hardware_ok=current.get("platform","").lower()==profile.get("platform","").lower() and current.get("sensor","").lower()==profile.get("sensor","").lower()
    add("hardware",hardware_ok,"Платформа та сенсор відповідають очікуваним" if hardware_ok else "Платформа або сенсор не відповідають очікуваним")
    fw_ok=not expected_firmware or current.get("firmware")==expected_firmware;add("firmware",fw_ok,"Спостережувана прошивка відповідає очікуваній" if fw_ok else "Спостережувана прошивка не відповідає очікуваній")
    same_identity=not before or (current.get("platform")==before.get("platform") and current.get("sensor")==before.get("sensor"));add("identity-continuity",same_identity,"Апаратну ідентичність збережено" if same_identity else "Апаратна ідентичність змінилася")
    return {"ok":all(c["ok"] for c in checks),"checks":checks,"identity":current}
