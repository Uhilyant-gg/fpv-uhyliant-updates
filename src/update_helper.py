import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from app.update_package import extract_verified_zip,verify_package
from updater_handoff import valid_handoff
a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--package',required=True);a.add_argument('--version',required=True);a.add_argument('--sha256',required=True);a.add_argument('--wait-pid',type=int,required=True);x=a.parse_args()
if not valid_handoff(x.root,x.package,x.version,x.sha256,x.wait_pid):raise SystemExit('invalid updater handoff')
r=Path(x.root).resolve();app=r/'app';cur=app/'current';old=app/'rollback'/'previous';stage_root=app/'staging';stage=stage_root/x.version;state=app/'launcher-state.json';data=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';data.mkdir(parents=True,exist_ok=True);log=data/'updater.log'
def note(msg):
 with log.open('a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S')+' update '+msg+'\n')
def fail(msg):note('ERROR '+msg);raise RuntimeError(msg)
def save_state(v):
 tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(v),encoding='utf-8');os.replace(tmp,state)
try:
 note('begin version='+x.version)
 for _ in range(120):
  try:os.kill(x.wait_pid,0);time.sleep(.25)
  except OSError:break
 else:fail('application did not exit before update timeout')
 pkg=Path(x.package).resolve()
 if not verify_package(pkg,x.sha256):fail('package digest mismatch at helper handoff')
 shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True,exist_ok=True)
 try:extract_verified_zip(pkg,stage,x.sha256)
 except ValueError as e:fail(str(e))
 payload=stage if (stage/'FPV-Uhyliant.exe').exists() else next((p for p in stage.iterdir() if p.is_dir() and (p/'FPV-Uhyliant.exe').exists()),None)
 if payload is None:fail('FPV-Uhyliant.exe missing from payload')
 test=subprocess.run([str(payload/'FPV-Uhyliant.exe'),'--self-test'],check=True,cwd=payload,capture_output=True,text=True,timeout=30)
 try:reported=json.loads(test.stdout.strip()).get('version')
 except (ValueError,AttributeError):reported=None
 if reported!=x.version:fail(f'payload version mismatch: expected {x.version}, got {reported!r}')
 if not verify_package(pkg,x.sha256):fail('package changed during staging')
 old.parent.mkdir(parents=True,exist_ok=True);shutil.rmtree(old,ignore_errors=True)
 if not cur.exists():fail('current application directory missing')
 note('validated package; switching current');os.replace(cur,old)
 try:os.replace(payload,cur)
 except Exception:
  if old.exists() and not cur.exists():os.replace(old,cur)
  raise
 save_state({'current':x.version,'pendingStartup':True,'packageSha256':x.sha256.lower(),'updatedAt':int(time.time())})
 for p in stage_root.iterdir():
  if p!=stage and p.name!='failed':shutil.rmtree(p,ignore_errors=True)
 note('switch complete; starting launcher');subprocess.Popen([str(r/'FPV-Uhyliant-Launcher.exe')],cwd=r,creationflags=getattr(subprocess,'DETACHED_PROCESS',0))
except Exception as e:note('failed '+repr(e));raise
