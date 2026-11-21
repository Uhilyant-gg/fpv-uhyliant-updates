"""Pure post-operation verification helpers. Hardware acquisition stays outside this module."""
from openipc_device import normalize_openipc_identity

def verify_post_flash(before, observed, profile, expected_firmware=""):
    current=normalize_openipc_identity(observed, observed.get("evidence",[]) if isinstance(observed,dict) else [])
    checks=[]
    def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
    add("rediscovered",bool(observed),"Пристрій повторно виявлено" if observed else "Пристрій не виявлено повторно")
    add("openipc",current.get("verified"),"Докази OpenIPC підтверджено" if current.get("verified") else "Докази OpenIPC недоступні")
    hardware_ok=bool(current.get("platform") and current.get("sensor") and current.get("platform","").lower()==profile.get("platform","").lower() and current.get("sensor","").lower()==profile.get("sensor","").lower())
    add("hardware",hardware_ok,"Платформа та сенсор відповідають очікуваним" if hardware_ok else "Платформа або сенсор не відповідають очікуваним")
    observed_firmware=str(current.get("firmware","")).strip();fw_ok=bool(observed_firmware) and (not expected_firmware or observed_firmware==expected_firmware)
    add("firmware",fw_ok,"Отримано фактично спостережувану версію прошивки" if fw_ok else ("Спостережувана прошивка не відповідає очікуваній" if observed_firmware else "Версію прошивки після оновлення не спостережено"))
    before_platform=str(before.get("platform","")).strip() if isinstance(before,dict) else "";before_sensor=str(before.get("sensor","")).strip() if isinstance(before,dict) else ""
    same_identity=bool(before_platform and before_sensor and current.get("platform","").lower()==before_platform.lower() and current.get("sensor","").lower()==before_sensor.lower())
    add("identity-continuity",same_identity,"Апаратну ідентичність збережено" if same_identity else "Апаратна ідентичність змінилася або попередня ідентичність неповна")
    return {"ok":all(c["ok"] for c in checks),"checks":checks,"identity":current,"expectedFirmware":str(expected_firmware or "")}
