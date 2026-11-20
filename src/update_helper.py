import argparse,json,os,shutil,subprocess,sys,time,zipfile
from pathlib import Path
a=argparse.ArgumentParser();a.add_argument('--root');a.add_argument('--package');a.add_argument('--version');a.add_argument('--wait-pid',type=int);x=a.parse_args();r=Path(x.root);app=r/'app';cur=app/'current';old=app/'rollback'/'previous';stage=app/'staging'/x.version
for _ in range(120):
 try:os.kill(x.wait_pid,0);time.sleep(.25)
 except OSError:break
shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
with zipfile.ZipFile(x.package) as z:
 for i in z.infolist():
  if stage.resolve() not in (stage/i.filename).resolve().parents:raise RuntimeError('unsafe zip')
 z.extractall(stage)
payload=stage if (stage/'main.py').exists() else next(p for p in stage.iterdir() if (p/'main.py').exists())
py=r/'.venv'/'Scripts'/'python.exe';subprocess.run([str(py),str(payload/'main.py'),'--self-test'],check=True,cwd=payload)
shutil.rmtree(old,ignore_errors=True);os.replace(cur,old);os.replace(payload,cur);(app/'launcher-state.json').write_text(json.dumps({'current':x.version,'pendingStartup':True}));subprocess.Popen([str(py),str(r/'launcher.py')],cwd=r)
