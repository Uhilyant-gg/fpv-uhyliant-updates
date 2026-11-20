import json,os,subprocess,sys,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;A=R/'app';C=A/'current';B=A/'rollback'/'previous';S=A/'launcher-state.json';D=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';OK=D/'startup-ok.json'
def py():p=R/'.venv'/'Scripts'/'python.exe';return p if p.exists() else Path(sys.executable)
def main():
 st=json.loads(S.read_text()) if S.exists() else {};pending=st.get('pendingStartup',False);token=os.urandom(16).hex();D.mkdir(parents=True,exist_ok=True);OK.unlink(missing_ok=True);p=subprocess.Popen([str(py()),str(C/'main.py'),'--install-root',str(R),'--startup-token',token],cwd=C)
 if pending:
  end=time.time()+25
  while time.time()<end and p.poll() is None:
   if OK.exists() and json.loads(OK.read_text()).get('token')==token:st['pendingStartup']=False;S.write_text(json.dumps(st));return p.wait()
   time.sleep(.25)
  try:p.kill()
  except:pass
  failed=A/'staging'/'failed';shutil.rmtree(failed,ignore_errors=True);os.replace(C,failed);os.replace(B,C);st['pendingStartup']=False;S.write_text(json.dumps(st));return subprocess.call([str(py()),str(C/'main.py'),'--install-root',str(R)],cwd=C)
 return p.wait()
if __name__=='__main__':raise SystemExit(main())
