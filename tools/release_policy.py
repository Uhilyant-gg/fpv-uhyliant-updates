"""Pure validation helpers for the release pipeline."""
import hashlib,re
from pathlib import Path
VERSION_RE=re.compile(r'^\d+\.\d+\.\d+$')
CHANNELS={'test','stable','development'}
def validate_release_inputs(version,channel,prerelease):
 if not VERSION_RE.fullmatch(version or ''):raise ValueError('invalid release version')
 if channel not in CHANNELS:raise ValueError('invalid release channel')
 if channel!='stable' and not prerelease:raise ValueError('non-stable channels must be prerelease')
 return True
def sha256_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def verify_sha256(path,expected):
 expected=(expected or '').strip().lower()
 return bool(re.fullmatch(r'[0-9a-f]{64}',expected)) and sha256_file(path)==expected
