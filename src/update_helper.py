import argparse,json,os,shutil,subprocess,time,zipfile
from pathlib import Path
a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--package',required=True);a.add_argument('--version',required=True);a.add_argument('--wait-pid',type=int,required=True);x=a.parse_args();r=Path(x.root).resolve();app=r/'app';cur=app/'current';old=app/'rollback'/'previous';stage=app/'staging'/x.version
for _ in range(120):
 try:os.kill(x.wait_pid,0);time.sleep(.25)
 except OSError:break
shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
with zipfile.ZipFile(x.package) as z:
 for i in z.infolist():
  target=(stage/i.filename).resolve()
  if target!=stage.resolve() and stage.resolve() not in target.parents:raise RuntimeError('unsafe zip')
 z.extractall(stage)
payload=stage if (stage/'FPV-Uhyliant.exe').exists() else next(p for p in stage.iterdir() if p.is_dir() and (p/'FPV-Uhyliant.exe').exists())
subprocess.run([str(payload/'FPV-Uhyliant.exe'),'--self-test'],check=True,cwd=payload)
shutil.rmtree(old,ignore_errors=True);old.parent.mkdir(parents=True,exist_ok=True)
if cur.exists():os.replace(cur,old)
os.replace(payload,cur)
(app/'launcher-state.json').write_text(json.dumps({'current':x.version,'pendingStartup':True}),encoding='utf-8')
subprocess.Popen([str(r/'FPV-Uhyliant-Launcher.exe')],cwd=r,creationflags=getattr(subprocess,'DETACHED_PROCESS',0))
