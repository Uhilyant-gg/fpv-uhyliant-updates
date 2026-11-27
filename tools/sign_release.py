import argparse, base64, json
from pathlib import Path
from cryptography.hazmat.primitives import serialization

def canonical(obj):
    obj=dict(obj);obj.pop('signature',None)
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')

ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--key',required=True);ap.add_argument('--key-id',required=True);a=ap.parse_args()
p=Path(a.manifest);obj=json.loads(p.read_text(encoding='utf-8'));obj.pop('signature',None)
key=serialization.load_pem_private_key(Path(a.key).read_bytes(),password=None)
obj['signature']={'algorithm':'Ed25519','keyId':a.key_id,'value':base64.b64encode(key.sign(canonical(obj))).decode('ascii')}
p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
print(p)
