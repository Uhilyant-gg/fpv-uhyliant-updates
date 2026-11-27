import json, math, os
from pathlib import Path
from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot
from home_dashboard import home_dashboard
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'; DATA.mkdir(parents=True,exist_ok=True)

class HomeDashboard(QObject):
 changed=Signal()
 def __init__(self,devices):
  super().__init__()
  self._devices=devices
  self._model=home_dashboard(devices.items,devices.streams)
  devices.changed.connect(self.refresh)
  devices.streamsChanged.connect(self.refresh)
  devices.discoveryChanged.connect(self.refresh)
 def refresh(self):
  self._model=home_dashboard(self._devices.items,self._devices.streams)
  self.changed.emit()
 @Property(str,notify=changed)
 def health(self):return self._model["health"]
 @Property(str,notify=changed)
 def title(self):return self._model["title"]
 @Property(str,notify=changed)
 def summary(self):return self._model["summary"]
 @Property(int,notify=changed)
 def deviceCount(self):return self._model["deviceCount"]
 @Property(int,notify=changed)
 def verifiedCount(self):return self._model["verifiedCount"]
 @Property(int,notify=changed)
 def warningCount(self):return self._model["warningCount"]
 @Property('QVariantMap',notify=changed)
 def nextAction(self):return dict(self._model["nextAction"])
class Station(QObject):
 changed=Signal(); notice=Signal(str)
 OSD_ENABLED_KEY="osd/station-enabled"
 OSD_OPACITY_KEY="osd/station-opacity"
 OSD_SCALE_KEY="osd/station-scale"
 OSD_POSITION_KEY="osd/station-position"
 OSD_POSITIONS=("top-left","top-right","bottom-left","bottom-right")
 OSD_DEFAULT_OPACITY=.58
 OSD_DEFAULT_SCALE=1.0
 OSD_DEFAULT_POSITION="top-left"
 def __init__(self,settings=None):
  super().__init__();self._settings=settings or QSettings("FPV-Uhyliant","FPV-Uhyliant");self._menu=False;self._video=False;self._osd='station';self._osd_enabled=self._read_osd_enabled();self._edit=False;self._opacity=self._read_osd_number(self.OSD_OPACITY_KEY,self.OSD_DEFAULT_OPACITY,.25,.8);self._scale=self._read_osd_number(self.OSD_SCALE_KEY,self.OSD_DEFAULT_SCALE,.85,1.3);self._position=self._read_osd_position();self._osd_settings_error="";self._armed=False;self._recording=False;self._streaming=False
 def _read_osd_enabled(self):
  value=self._settings.value(self.OSD_ENABLED_KEY,True)
  return str(value).strip().lower() not in ("0","false","no","off")
 def _read_osd_number(self,key,default,minimum,maximum):
  try:value=float(self._settings.value(key,default))
  except (TypeError,ValueError):return default
  if not math.isfinite(value):return default
  return max(minimum,min(maximum,value))
 def _read_osd_position(self):
  value=str(self._settings.value(self.OSD_POSITION_KEY,self.OSD_DEFAULT_POSITION))
  return value if value in self.OSD_POSITIONS else self.OSD_DEFAULT_POSITION
 @Property(bool,notify=changed)
 def menuOpen(self):return self._menu
 @Property(bool,notify=changed)
 def videoRunning(self):return self._video
 @Property(str,notify=changed)
 def osdSource(self):return self._osd
 @Property(bool,notify=changed)
 def osdEnabled(self):return self._osd_enabled
 @Property(bool,notify=changed)
 def osdEdit(self):return self._edit
 @Property(float,notify=changed)
 def osdOpacity(self):return self._opacity
 @Property(float,notify=changed)
 def osdScale(self):return self._scale
 @Property(str,notify=changed)
 def osdPosition(self):return self._position
 @Property(str,notify=changed)
 def osdSettingsError(self):return self._osd_settings_error
 @Slot()
 def toggleMenu(self):self._menu=not self._menu;self.changed.emit()
 @Slot()
 def toggleVideo(self):self._video=not self._video;self.changed.emit()
 @Slot(str)
 def setOSDSource(self,v):self._osd=v;self.changed.emit()
 @Slot(bool)
 def setOSDEnabled(self,value):
  enabled=bool(value)
  if enabled==self._osd_enabled:return
  self._osd_enabled=enabled;self._settings.setValue(self.OSD_ENABLED_KEY,enabled);self._save_osd_settings();self.changed.emit()
 @Slot(bool)
 def setOSDEdit(self,v):self._edit=v;self.changed.emit()
 @Slot(float,float,result=bool)
 def setOSDStyle(self,o,s):
  if not math.isfinite(o) or not math.isfinite(s) or not .25<=o<=.8 or not .85<=s<=1.3:return False
  self._opacity=o;self._scale=s;self._settings.setValue(self.OSD_OPACITY_KEY,o);self._settings.setValue(self.OSD_SCALE_KEY,s);self._save_osd_settings();self.changed.emit();return self._osd_settings_error==""
 @Slot(str,result=bool)
 def setOSDPosition(self,value):
  if value not in self.OSD_POSITIONS:return False
  self._position=value;self._settings.setValue(self.OSD_POSITION_KEY,value);self._save_osd_settings();self.changed.emit();return self._osd_settings_error==""
 @Slot()
 def resetOSDStyle(self):
  self._opacity=self.OSD_DEFAULT_OPACITY;self._scale=self.OSD_DEFAULT_SCALE;self._position=self.OSD_DEFAULT_POSITION
  self._settings.setValue(self.OSD_OPACITY_KEY,self._opacity);self._settings.setValue(self.OSD_SCALE_KEY,self._scale);self._settings.setValue(self.OSD_POSITION_KEY,self._position);self._save_osd_settings();self.changed.emit()
 def _save_osd_settings(self):
  self._settings.sync()
  self._osd_settings_error="Не вдалося зберегти налаштування OSD. Перевірте доступ до папки даних." if self._settings.status()!=QSettings.NoError else ""
 @Slot(str)
 def action(self,v):self.notice.emit(v)
 def canInstallUpdate(self):
  r=[]
  if self._armed:r.append('автопілот озброєний')
  if self._recording:r.append('активний запис')
  if self._streaming:r.append('активна трансляція')
  return (not r,'Неможливо оновити: '+', '.join(r) if r else '')
