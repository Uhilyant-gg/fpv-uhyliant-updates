import argparse, base64, hashlib, json, urllib.parse
from pathlib import Path
from cryptography.hazmat.primitives import serialization


def canonical(o):
    d = dict(o)
    d.pop('signature', None)
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument('--channel', default='test')
ap.add_argument('--package')
a = ap.parse_args()
root = Path(__file__).resolve().parents[1]
ch = root / a.channel
m = json.loads((ch / 'release.json').read_text(encoding='utf-8'))
sig = m['signature']
key = serialization.load_pem_public_key((ch / 'release-public-key.pem').read_bytes())
key.verify(base64.b64decode(sig['value']), canonical(m))
u = urllib.parse.urlparse(m['package']['url'])
assert u.scheme == 'https' and u.hostname
if a.package:
    pkg = Path(a.package)
    assert pkg.is_file()
    assert sha(pkg) == m['package']['sha256']
else:
    pkg = ch / 'packages' / m['package']['file']
    if pkg.is_file():
        assert sha(pkg) == m['package']['sha256']
print('repository verify: OK', a.channel, m['version'])
