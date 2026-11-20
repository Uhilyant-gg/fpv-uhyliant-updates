import argparse, hashlib, json, shutil
from pathlib import Path

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

ap=argparse.ArgumentParser();ap.add_argument('--channel',choices=['test','stable','development'],required=True);ap.add_argument('--version',required=True);ap.add_argument('--build',type=int,required=True);ap.add_argument('--package',required=True);ap.add_argument('--base-url',required=True);ap.add_argument('--notes',nargs='*',default=[]);a=ap.parse_args()
root=Path(__file__).resolve().parents[1];ch=root/a.channel;pkg=Path(a.package);dest=ch/'packages'/pkg.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pkg,dest)
obj={'product':'FPV-Uhyliant','channel':a.channel,'version':a.version,'build':a.build,'mandatory':False,'minimumUpdaterVersion':'1.5.0','package':{'file':dest.name,'url':a.base_url.rstrip('/')+f'/{a.channel}/packages/{dest.name}','sha256':sha256(dest)},'releaseNotes':a.notes}
out=ch/'release.unsigned.json';out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding='utf-8');print(out)
