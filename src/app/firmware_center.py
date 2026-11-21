"""Safety gate for OpenIPC firmware operations. No destructive flashing is performed here."""
from PySide6.QtCore import QObject, Property, Signal, Slot

SUPPORTED_PROFILES={
    "ssc30kq-imx335":{"platform":"ssc30kq","sensor":"imx335"},
}
MODES=("primary","upgrade","recovery-fullflash")

class FirmwareCenter(QObject):
    changed=Signal()
    def __init__(self,devices):
        super().__init__();self.devices=devices;self._result=self._empty()
    def _empty(self):return {"ready":False,"deviceId":"","profile":"","mode":"","checks":[],"reason":"Не виконано pre-check"}
    @Property("QVariantMap",notify=changed)
    def result(self):return dict(self._result)
    @Property("QStringList",constant=True)
    def profiles(self):return list(SUPPORTED_PROFILES)
    @Property("QStringList",constant=True)
    def modes(self):return list(MODES)
    @Slot(str,str,str,bool,bool,bool,result=bool)
    def precheck(self,device_id,profile,mode,image_integrity,recovery_ready,layout_verified):
        device=next((d for d in self.devices.items if d.get("id")==device_id),None);identity=(device or {}).get("openipcIdentity") or {};target=SUPPORTED_PROFILES.get(profile);checks=[]
        def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
        add("device",device is not None,"Пристрій знайдено" if device else "Пристрій не знайдено")
        add("openipc",bool(identity.get("verified")),"OpenIPC identity verified" if identity.get("verified") else "OpenIPC identity не підтверджено")
        add("profile",target is not None,"Firmware profile відомий" if target else "Невідомий firmware profile")
        compatible=bool(target and identity.get("platform","").lower()==target["platform"] and identity.get("sensor","").lower()==target["sensor"])
        add("hardware",compatible,"Platform/sensor відповідають profile" if compatible else "Platform/sensor не підтверджують сумісність")
        add("layout",layout_verified,"Flash layout перевірено" if layout_verified else "Flash layout не перевірено")
        add("image",image_integrity,"Image integrity перевірено" if image_integrity else "Image integrity не перевірено")
        add("recovery",recovery_ready,"Recovery path готовий" if recovery_ready else "Recovery path не підтверджено")
        mode_ok=mode in MODES;add("mode",mode_ok,"Режим відомий" if mode_ok else "Невідомий режим")
        fullflash_ok=mode!="recovery-fullflash" or bool(identity.get("verified"));add("fullflash",fullflash_ok,"Fullflash gate дозволено" if fullflash_ok else "Fullflash лише для verified compatible OpenIPC")
        ready=all(c["ok"] for c in checks);self._result={"ready":ready,"deviceId":device_id,"profile":profile,"mode":mode,"checks":checks,"reason":"Готово до наступного етапу" if ready else "Destructive flashing заблоковано"};self.changed.emit();return ready
    @Slot()
    def reset(self):self._result=self._empty();self.changed.emit()
