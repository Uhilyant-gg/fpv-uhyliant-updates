import argparse,base64,json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
a=argparse.ArgumentParser();a.add_argument('manifest');a.add_argument('--key',required=True);x=a.parse_args();p=Path(x.manifest);o=json.loads(p.read_text());o.pop('signature',None);d=json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();k=serialization.load_pem_private_key(Path(x.key).read_bytes(),None);o['signature']={'algorithm':'Ed25519','keyId':'fpv-uhyliant-production-v1','value':base64.b64encode(k.sign(d)).decode()};p.write_text(json.dumps(o,ensure_ascii=False,indent=2))
