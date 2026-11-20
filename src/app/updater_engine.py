import base64,hashlib,json,os,subprocess,urllib.request
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot,QThread,QCoreApplication,QTimer
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from version import VERSION
KEY_ID='fpv-uhyliant-production-v1';HERE=Path(__file__).resolve().parent;PUB=HERE/'security/production-v1-public.pem';DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';UP=DATA/'updates';DEFAULT='https://<scrubbed-url-domain>/fpv-uhyliant-updates/test/release.json'
def canon(o):d=dict(o);d.pop('signature',None);return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def verify(o):
 s=o.get('signature') or {}
 if s.get('algorithm')!='Ed25519' or s.get('keyId')!=KEY_ID:raise RuntimeError('Недовірений підпис manifest')
 try:serialization.load_pem_public_key(PUB.read_bytes()).verify(base64.b64decode(s['value'],validate=True),canon(o))
 except (InvalidSignature,ValueError,KeyError) as e:raise RuntimeError('Підпис manifest не пройшов перевірку') from e
def vt(v):return tuple(int(x) for x in v.split('-')[0].split('.'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
class W(QThread):
 done=Signal(bool,object);progress=Signal(int,str)
 def __init__(self,a,p):super().__init__();self.a=a;self.p=p
 def run(self):
  try:
   if self.a=='check':
    with urllib.request.urlopen(self.p['url'],timeout=15) as r:o=json.loads(r.read(2097152).decode())
    verify(o);self.done.emit(True,o);return
   o=self.p['m'];pkg=o['package'];UP.mkdir(parents=True,exist_ok=True);t=UP/pkg['file']
   with urllib.request.urlopen(pkg['url'],timeout=60) as r,open(t,'wb') as f:
    total=int(r.headers.get('Content-Length') or 0);n=0
    while True:
     b=r.read(524288)
     if not b:break
     f.write(b);n+=len(b);self.progress.emit(int(n*100/total) if total else 0,f'{n//1048576} MB')
   if sha(t)!=pkg['sha256']:t.unlink(missing_ok=True);raise RuntimeError('SHA-256 пакета не збігається')
   ready={'version':o['version'],'package':str(t)};(UP/'ready.json').write_text(json.dumps(ready),encoding='utf-8');self.done.emit(True,ready)
  except Exception as e:self.done.emit(False,str(e))
class Updater(QObject):
 changed=Signal();progressChanged=Signal()
 def __init__(self,root=None,guard=None):super().__init__();self.root=Path(root).resolve() if root else None;self.guard=guard or (lambda:(True,''));self.url=DEFAULT;self.state='idle';self.status='Готово';self.available='';self.notes=[];self.p=0;self.m={};self.w=None
 @Property(str,constant=True)
 def currentVersion(self):return VERSION
 @Property(str,notify=changed)
 def manifestUrl(self):return self.url
 @Property(str,notify=changed)
 def updateState(self):return self.state
 @Property(str,notify=changed)
 def updateStatus(self):return self.status
 @Property(str,notify=changed)
 def availableVersion(self):return self.available
 @Property('QStringList',notify=changed)
 def releaseNotes(self):return self.notes
 @Property(int,notify=progressChanged)
 def progress(self):return self.p
 @Property(bool,notify=changed)
 def installReady(self):return self.state=='ready' and self.root is not None and (self.root/'FPV-Uhyliant-Update.exe').exists()
 @Slot()
 def check(self):self._start('check',{'url':self.url},'Перевірка підписаного manifest')
 @Slot()
 def download(self):
  if self.m:self._start('download',{'m':self.m},'Завантаження пакета')
 @Slot()
 def install(self):
  ok,why=self.guard()
  if not ok:self.state='blocked';self.status=why;self.changed.emit();return
  if not self.installReady:self.state='error';self.status='Компонент оновлення недоступний';self.changed.emit();return
  r=json.loads((UP/'ready.json').read_text(encoding='utf-8'));helper=self.root/'FPV-Uhyliant-Update.exe';subprocess.Popen([str(helper),'--root',str(self.root),'--package',r['package'],'--version',r['version'],'--wait-pid',str(os.getpid())],cwd=self.root,creationflags=getattr(subprocess,'DETACHED_PROCESS',0));QTimer.singleShot(300,QCoreApplication.quit)
 def _start(self,a,p,s):self.state=a;self.status=s;self.p=0;self.changed.emit();self.w=W(a,p);self.w.progress.connect(self._prog);self.w.done.connect(lambda ok,d:self._done(a,ok,d));self.w.start()
 def _prog(self,p,s):self.p=p;self.status=s;self.progressChanged.emit();self.changed.emit()
 def _done(self,a,ok,d):
  if not ok:self.state='error';self.status=str(d)
  elif a=='check':self.m=d;self.available=d['version'];self.notes=d.get('releaseNotes',[]);self.state='available' if vt(d['version'])>vt(VERSION) else 'current';self.status='Оновлення доступне' if self.state=='available' else 'Версія актуальна'
  else:self.state='ready';self.status='Пакет перевірено і готово до установки'
  self.changed.emit()
