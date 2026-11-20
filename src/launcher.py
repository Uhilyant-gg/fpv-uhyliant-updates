import json,os,subprocess,sys,time,shutil
from pathlib import Path
R=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
A=R/'app';C=A/'current';B=A/'rollback'/'previous';S=A/'launcher-state.json';D=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';OK=D/'startup-ok.json';LOG=D/'updater.log'
def note(msg):
 D.mkdir(parents=True,exist_ok=True)
 with LOG.open('a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S')+' launcher '+msg+'\n')
def load_state():
 try:return json.loads(S.read_text(encoding='utf-8')) if S.exists() else {}
 except Exception:return {}
def save_state(st):
 tmp=S.with_suffix('.tmp');tmp.write_text(json.dumps(st),encoding='utf-8');os.replace(tmp,S)
def run_current(token=None):
 exe=C/'FPV-Uhyliant.exe'
 if not exe.is_file():raise RuntimeError('current FPV-Uhyliant.exe missing')
 args=[str(exe),'--install-root',str(R)]
 if token:args+=['--startup-token',token]
 return subprocess.Popen(args,cwd=C)
def main():
 st=load_state();pending=bool(st.get('pendingStartup'));token=os.urandom(16).hex();D.mkdir(parents=True,exist_ok=True);OK.unlink(missing_ok=True)
 try:p=run_current(token if pending else None)
 except Exception as e:
  note('launch failed '+repr(e))
  if pending and B.exists() and not C.exists():os.replace(B,C);return subprocess.call([str(C/'FPV-Uhyliant.exe'),'--install-root',str(R)],cwd=C)
  raise
 if pending:
  note('pending startup verification for '+str(st.get('current','unknown')));end=time.time()+30
  while time.time()<end and p.poll() is None:
   try:
    ack=json.loads(OK.read_text(encoding='utf-8')) if OK.exists() else {}
    if ack.get('token')==token and ack.get('version')==st.get('current'):
     st['pendingStartup']=False;st['lastGood']=st.get('current');save_state(st);note('startup OK '+str(st.get('current')));return p.wait()
   except (OSError,ValueError):pass
   time.sleep(.25)
  try:p.kill()
  except OSError:pass
  note('startup verification failed; rollback')
  failed=A/'staging'/'failed';shutil.rmtree(failed,ignore_errors=True)
  if C.exists():os.replace(C,failed)
  if B.exists():os.replace(B,C)
  else:raise RuntimeError('rollback copy missing')
  st['pendingStartup']=False;st['rollbackAt']=int(time.time());save_state(st)
  return subprocess.call([str(C/'FPV-Uhyliant.exe'),'--install-root',str(R)],cwd=C)
 return p.wait()
if __name__=='__main__':raise SystemExit(main())
