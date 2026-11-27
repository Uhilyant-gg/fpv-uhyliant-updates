import json, os
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'; DATA.mkdir(parents=True,exist_ok=True)
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
