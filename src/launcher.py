import json,os,subprocess,sys,time,shutil
from pathlib import Path
R=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
A=R/'app';C=A/'current';B=A/'rollback'/'previous';S=A/'launcher-state.json';D=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';OK=D/'startup-ok.json'
def run_current(token=None):
 exe=C/'FPV-Uhyliant.exe';args=[str(exe),'--install-root',str(R)]
 if token:args+=['--startup-token',token]
 return subprocess.Popen(args,cwd=C)
def main():
 st=json.loads(S.read_text(encoding='utf-8')) if S.exists() else {};pending=st.get('pendingStartup',False);token=os.urandom(16).hex();D.mkdir(parents=True,exist_ok=True);OK.unlink(missing_ok=True);p=run_current(token)
 if pending:
  end=time.time()+25
  while time.time()<end and p.poll() is None:
   try:
    if OK.exists() and json.loads(OK.read_text(encoding='utf-8')).get('token')==token:st['pendingStartup']=False;S.write_text(json.dumps(st),encoding='utf-8');return p.wait()
   except (OSError,ValueError):pass
   time.sleep(.25)
  try:p.kill()
  except OSError:pass
  failed=A/'staging'/'failed';shutil.rmtree(failed,ignore_errors=True)
  if C.exists():os.replace(C,failed)
  if B.exists():os.replace(B,C)
  st['pendingStartup']=False;S.write_text(json.dumps(st),encoding='utf-8');return subprocess.call([str(C/'FPV-Uhyliant.exe'),'--install-root',str(R)],cwd=C)
 return p.wait()
if __name__=='__main__':raise SystemExit(main())
