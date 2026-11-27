import base64,hashlib,json,os,re,subprocess,urllib.parse,urllib.request
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from PySide6.QtCore import QCoreApplication,QObject,Property,QThread,QTimer,Signal,Slot
from version import VERSION
from updater_install import helper_args,install_decision,stage_ready_package
KEY_ID='fpv-uhyliant-production-v1';HERE=Path(__file__).resolve().parent;PUB=HERE/'security/production-v1-public.pem';DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';UP=DATA/'updates';VERSION_RE=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$')
def _manifest_url():scheme=''.join(map(chr,[104,116,116,112,115,58,47,47]));host=''.join(map(chr,[117,104,105,108,121,97,110,116,45,103,103,46,103,105,116,104,117,98,46,105,111]));return scheme+host+'/fpv-uhyliant-updates/test/release.json'
DEFAULT=_manifest_url()
def canon(o):d=dict(o);d.pop('signature',None);return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def vt(v):
 if not isinstance(v,str) or not VERSION_RE.fullmatch(v):raise RuntimeError('Версія оновлення має некоректний формат')
 return tuple(int(x) for x in v.split('-',1)[0].split('.'))
def https_url(v,label):
 u=urllib.parse.urlparse(v)
 if u.scheme!='https' or not u.hostname or u.username or u.password:raise RuntimeError(f'Некоректний HTTPS URL для {label}')
def verify(o):
 if not isinstance(o,dict):raise RuntimeError('Маніфест має некоректний формат')
 s=o.get('signature') or {};pkg=o.get('package')
 if s.get('algorithm')!='Ed25519' or s.get('keyId')!=KEY_ID:raise RuntimeError('Недовірений підпис маніфесту')
 if not isinstance(pkg,dict):raise RuntimeError('Маніфест не містить опис пакета')
 vt(o.get('version'));https_url(pkg.get('url',''),'пакета')
 if not isinstance(pkg.get('file'),str) or not pkg['file'] or Path(pkg['file']).name!=pkg['file']:raise RuntimeError('Некоректне ім’я файла пакета')
 if not isinstance(pkg.get('sha256'),str) or not re.fullmatch(r'[0-9a-fA-F]{64}',pkg['sha256']):raise RuntimeError('Некоректний SHA-256 пакета')
 try:serialization.load_pem_public_key(PUB.read_bytes()).verify(base64.b64decode(s['value'],validate=True),canon(o))
 except (InvalidSignature,ValueError,KeyError,OSError) as e:raise RuntimeError('Підпис маніфесту не пройшов перевірку') from e
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load_ready(expected_manifest=None):
 try:r=json.loads((UP/'ready.json').read_text(encoding='utf-8'))
 except (OSError,ValueError,TypeError) as e:raise RuntimeError('Некоректний стан завантаженого оновлення') from e
 if not isinstance(r,dict) or set(r)!={'version','package','sha256'} or not all(isinstance(r.get(k),str) for k in ('version','package','sha256')):raise RuntimeError('Некоректний стан завантаженого оновлення')
 vt(r['version']);package=Path(r['package']).resolve();updates=UP.resolve()
 try:package.relative_to(updates)
 except ValueError as e:raise RuntimeError('Пакет оновлення знаходиться поза каталогом оновлень') from e
 if package.parent!=updates:raise RuntimeError('Пакет оновлення має бути безпосередньо в каталозі оновлень')
 if not re.fullmatch(r'[0-9a-f]{64}',r['sha256'].lower()):raise RuntimeError('Некоректний SHA-256 у стані готовності')
 if not package.is_file() or sha(package).lower()!=r['sha256'].lower():raise RuntimeError('Завантажений пакет змінився після перевірки')
 if expected_manifest:
  pkg=expected_manifest.get('package') or {};expected=str(pkg.get('sha256','')).lower()
  if r['version']!=expected_manifest.get('version') or package.name!=pkg.get('file') or r['sha256'].lower()!=expected:raise RuntimeError('Завантажений пакет не відповідає перевіреному маніфесту')
 return {'version':r['version'],'package':str(package),'sha256':r['sha256'].lower()}
def validate_install_root(root):
 if root is None:return None
 r=Path(root).resolve();helper=r/'FPV-Uhyliant-Update.exe';launcher=r/'FPV-Uhyliant-Launcher.exe';current=r/'app'/'current'/'FPV-Uhyliant.exe'
 return r if helper.is_file() and launcher.is_file() and current.is_file() else None
UPDATE_VALIDATION_MESSAGES={
 'Версія оновлення має некоректний формат':'Оновлення містить некоректну версію. Його перевірку зупинено.',
 'Некоректний HTTPS URL для маніфесту':'Не вдалося перевірити захищене посилання на оновлення.',
 'Некоректний HTTPS URL для пакета':'Не вдалося перевірити захищене посилання на оновлення.',
 'Маніфест має некоректний формат':'Не вдалося прочитати інформацію про оновлення. Спробуйте ще раз пізніше.',
 'Недовірений підпис маніфесту':'Не вдалося підтвердити джерело оновлення. Завантаження зупинено.',
 'Маніфест не містить опис пакета':'В інформації про оновлення бракує потрібних даних. Спробуйте пізніше.',
 'Некоректне ім’я файла пакета':'Назва файла оновлення не пройшла перевірку. Завантаження зупинено.',
 'Некоректний SHA-256 пакета':'Файл оновлення не пройшов перевірку цілісності. Завантаження зупинено.',
 'Підпис маніфесту не пройшов перевірку':'Не вдалося підтвердити джерело оновлення. Завантаження зупинено.',
 'Некоректний стан завантаженого оновлення':'Дані завантаженого оновлення пошкоджені. Завантажте його ще раз.',
 'Пакет оновлення знаходиться поза каталогом оновлень':'Файл оновлення знаходиться у непідтримуваній папці. Встановлення зупинено.',
 'Пакет оновлення має бути безпосередньо в каталозі оновлень':'Файл оновлення знаходиться у непідтримуваній папці. Встановлення зупинено.',
 'Некоректний SHA-256 у стані готовності':'Файл оновлення не пройшов перевірку цілісності. Встановлення зупинено.',
 'Завантажений пакет змінився після перевірки':'Файл оновлення змінився після перевірки. Завантажте його ще раз.',
 'Завантажений пакет не відповідає перевіреному маніфесту':'Файл не відповідає перевіреній версії оновлення. Завантажте його ще раз.',
 'SHA-256 пакета не збігається':'Файл оновлення не пройшов перевірку цілісності. Завантажте його ще раз.',
 'Некоректний стан пакета для staging':'Не вдалося підготувати оновлення до встановлення. Спробуйте ще раз.',
 'Пакет не пройшов перевірку перед staging':'Файл оновлення не пройшов перевірку цілісності. Встановлення зупинено.',
 'Пакет змінився під час staging':'Файл оновлення змінився під час підготовки. Завантажте його ще раз.',
 'Некоректний стан пакета для запуску updater':'Не вдалося підготувати оновлення до встановлення. Спробуйте ще раз.',
 'Некоректний PID для запуску updater':'Не вдалося підготувати оновлення до встановлення. Спробуйте ще раз.',
}
def human_update_error(action,error):
 if isinstance(error,RuntimeError):return UPDATE_VALIDATION_MESSAGES.get(str(error),'Не вдалося безпечно перевірити оновлення. Операцію зупинено.')
 if isinstance(error,(urllib.error.URLError,TimeoutError,ConnectionError)):
  return 'Не вдалося перевірити оновлення. Перевірте мережу і спробуйте ще раз.' if action=='check' else 'Не вдалося завантажити оновлення. Перевірте мережу і спробуйте ще раз.'
 if isinstance(error,OSError):return 'Не вдалося зберегти оновлення. Перевірте доступ до диска і вільне місце.'
 return 'Не вдалося завершити операцію оновлення. Перевірте мережу і спробуйте ще раз.'
class W(QThread):
 done=Signal(bool,object);progress=Signal(int,str)
 def __init__(self,a,p):super().__init__();self.a=a;self.p=p
 def run(self):
  try:
   if self.a=='check':
    https_url(self.p['url'],'маніфесту')
    with urllib.request.urlopen(self.p['url'],timeout=15) as r:o=json.loads(r.read(2097152).decode('utf-8'))
    verify(o);self.done.emit(True,o);return
   o=self.p['m'];verify(o);pkg=o['package'];UP.mkdir(parents=True,exist_ok=True);t=UP/pkg['file'];part=t.with_suffix(t.suffix+'.part');part.unlink(missing_ok=True)
   try:
    with urllib.request.urlopen(pkg['url'],timeout=60) as r,part.open('wb') as f:
     total=int(r.headers.get('Content-Length') or 0);n=0
     while True:
      b=r.read(524288)
      if not b:break
      if self.isInterruptionRequested():raise RuntimeError('Завантаження скасовано')
      f.write(b);n+=len(b);self.progress.emit(int(n*100/total) if total else 0,f'{n//1048576} МБ')
    digest=sha(part).lower()
    if digest!=pkg['sha256'].lower():raise RuntimeError('SHA-256 пакета не збігається')
    os.replace(part,t)
   except Exception:part.unlink(missing_ok=True);raise
   ready={'version':o['version'],'package':str(t),'sha256':digest};tmp=UP/'ready.tmp';tmp.write_text(json.dumps(ready),encoding='utf-8');os.replace(tmp,UP/'ready.json');self.done.emit(True,ready)
  except Exception as e:self.done.emit(False,human_update_error(self.a,e))
class Updater(QObject):
 changed=Signal();progressChanged=Signal()
 def __init__(self,root=None,guard=None,network=True):super().__init__();self.network=network;self.root=validate_install_root(root);self.guard=guard or (lambda:(True,''));self.url=DEFAULT;self.state='idle';self.status='Готово';self.available='';self.notes=[];self.p=0;self.m={};self.w=None
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
 def busy(self):return self.w is not None and self.w.isRunning()
 @Property(bool,notify=changed)
 def installReady(self):return self.state=='ready' and self.root is not None
 @Slot()
 def check(self):
  if not self.network:self.state='idle';self.status='Перевірку оновлень вимкнено в цьому режимі';self.changed.emit();return
  self._start('check',{'url':self.url},'Перевірка підписаного маніфесту')
 def shutdown(self,timeout_ms=3000):
  """Stop a running check/download before the application exits.

  A QThread destroyed while still running aborts the whole process, so the
  worker is asked to stop and given a bounded time to finish.
  """
  w=self.w
  if w is None or not w.isRunning():return True
  w.requestInterruption();return w.wait(timeout_ms)
 @Slot()
 def download(self):
  if self.m:self._start('download',{'m':self.m},'Завантаження пакета')
 @Slot()
 def install(self):
  ok,why=self.guard();decision=install_decision(self.busy,ok,self.installReady)
  if decision=='busy':self.status='Дочекайтеся завершення поточної операції';self.changed.emit();return
  if decision=='blocked':self.state='blocked';self.status=why;self.changed.emit();return
  if decision=='unavailable':self.state='error';self.status='Компонент оновлення недоступний: запустіть встановлену програму через FPV-Uhyliant-Launcher.exe';self.changed.emit();return
  try:r=stage_ready_package(self.root,load_ready(self.m));args=helper_args(self.root/'FPV-Uhyliant-Update.exe',self.root,r,os.getpid());subprocess.Popen(args,cwd=self.root,creationflags=getattr(subprocess,'DETACHED_PROCESS',0))
  except RuntimeError as e:self.state='error';self.status=human_update_error('install',e);self.changed.emit();return
  except (OSError,ValueError) as e:self.state='error';self.status=human_update_error('install',e);self.changed.emit();return
  self.state='installing';self.status='Встановлення оновлення розпочато';self.changed.emit()
  QTimer.singleShot(300,QCoreApplication.quit)
 def _start(self,a,p,s):
  if self.busy:self.status='Операція оновлення вже виконується';self.changed.emit();return
  self.state=a;self.status=s;self.p=0;self.changed.emit();self.progressChanged.emit();w=W(a,p);self.w=w;w.progress.connect(self._prog);w.done.connect(lambda ok,d,current=w:self._done(a,current,ok,d));w.finished.connect(lambda current=w:self._finished(current));w.start()
 def _prog(self,p,s):self.p=p;self.status=s;self.progressChanged.emit();self.changed.emit()
 def _done(self,a,w,ok,d):
  if w is not self.w:return
  if not ok:self.state='error';self.status=str(d)
  elif a=='check':self.m=d;self.available=d['version'];self.notes=d.get('releaseNotes',[]);self.state='available' if vt(d['version'])>vt(VERSION) else 'current';self.status='Оновлення доступне' if self.state=='available' else 'Версія актуальна'
  else:self.state='ready';self.status='Пакет перевірено і готовий до встановлення'
  self.changed.emit()
 def _finished(self,w):
  if w is self.w:self.w=None
  w.deleteLater();self.changed.emit()
