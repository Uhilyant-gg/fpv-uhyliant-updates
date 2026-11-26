import json, os
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot
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
 def __init__(self):
  super().__init__();self._menu=False;self._video=False;self._osd='station';self._edit=False;self._opacity=.58;self._scale=.82;self._armed=False;self._recording=False;self._streaming=False
 @Property(bool,notify=changed)
 def menuOpen(self):return self._menu
 @Property(bool,notify=changed)
 def videoRunning(self):return self._video
 @Property(str,notify=changed)
 def osdSource(self):return self._osd
 @Property(bool,notify=changed)
 def osdEdit(self):return self._edit
 @Property(float,notify=changed)
 def osdOpacity(self):return self._opacity
 @Property(float,notify=changed)
 def osdScale(self):return self._scale
 @Slot()
 def toggleMenu(self):self._menu=not self._menu;self.changed.emit()
 @Slot()
 def toggleVideo(self):self._video=not self._video;self.changed.emit()
 @Slot(str)
 def setOSDSource(self,v):self._osd=v;self.changed.emit()
 @Slot(bool)
 def setOSDEdit(self,v):self._edit=v;self.changed.emit()
 @Slot(float,float)
 def setOSDStyle(self,o,s):self._opacity=o;self._scale=s;self.changed.emit()
 @Slot(str)
 def action(self,v):self.notice.emit(v)
 def canInstallUpdate(self):
  r=[]
  if self._armed:r.append('автопілот озброєний')
  if self._recording:r.append('активний запис')
  if self._streaming:r.append('активна трансляція')
  return (not r,'Неможливо оновити: '+', '.join(r) if r else '')
