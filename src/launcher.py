import json,os,subprocess,sys,time,shutil,re
from pathlib import Path
from startup_ack import pending_ack
from rollback_plan import rollback_preconditions,rolled_back_state
R=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
A=R/'app';C=A/'current';B=A/'rollback'/'previous';S=A/'launcher-state.json';D=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';OK=D/'startup-ok.json';LOG=D/'updater.log';SHA_RE=re.compile(r'^[0-9a-f]{64}$')
def note(msg):
 D.mkdir(parents=True,exist_ok=True)
 with LOG.open('a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S')+' launcher '+msg+'\n')
def load_state():
 try:
  state=json.loads(S.read_text(encoding='utf-8')) if S.exists() else {}
  return state if isinstance(state,dict) else {}
 except Exception:return {}
def save_state(st):
 S.parent.mkdir(parents=True,exist_ok=True);tmp=S.with_suffix('.tmp');tmp.write_text(json.dumps(st),encoding='utf-8');os.replace(tmp,S)
def valid_pending(st):return set(st)=={'current','pendingStartup','packageSha256','updatedAt'} and st.get('pendingStartup') is True and isinstance(st.get('current'),str) and bool(st['current']) and isinstance(st.get('packageSha256'),str) and bool(SHA_RE.fullmatch(st['packageSha256'])) and type(st.get('updatedAt')) is int and st['updatedAt']>0
def run_current(token=None):
 exe=C/'FPV-Uhyliant.exe'
 if not exe.is_file():raise RuntimeError('current FPV-Uhyliant.exe missing')
 args=[str(exe),'--install-root',str(R)]
 if token:args+=['--startup-token',token]
 return subprocess.Popen(args,cwd=C)
def rollback(st,reason):
 note(reason+'; rollback');action=rollback_preconditions(C.exists(),B.exists())
 if action=='missing-rollback':raise RuntimeError('rollback copy missing')
 failed=A/'staging'/'failed';shutil.rmtree(failed,ignore_errors=True)
 if action=='replace-current':os.replace(C,failed)
 os.replace(B,C)
 save_state(rolled_back_state(st,int(time.time())));return subprocess.call([str(C/'FPV-Uhyliant.exe'),'--install-root',str(R)],cwd=C)
def main():
 st=load_state();pending=bool(st.get('pendingStartup'));token=os.urandom(16).hex();D.mkdir(parents=True,exist_ok=True);OK.unlink(missing_ok=True)
 if pending and not valid_pending(st):return rollback(st,'invalid pending startup state')
 try:p=run_current(token if pending else None)
 except Exception as e:
  note('launch failed '+repr(e))
  if pending:return rollback(st,'pending launch failed')
  raise
 if pending:
  note('pending startup verification for '+str(st.get('current','unknown')));end=time.time()+30
  while time.time()<end and p.poll() is None:
   try:
    ack=json.loads(OK.read_text(encoding='utf-8')) if OK.exists() else {}
    if pending_ack(ack,token,st.get('current')):
     st['pendingStartup']=False;st['lastGood']=st.get('current');st['lastGoodPackageSha256']=st.get('packageSha256');save_state(st);note('startup OK '+str(st.get('current')));return p.wait()
   except (OSError,ValueError,TypeError):pass
   time.sleep(.25)
  try:p.kill()
  except OSError:pass
  return rollback(st,'startup verification failed')
 return p.wait()
if __name__=='__main__':raise SystemExit(main())
