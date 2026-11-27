"""Pure guards for OTA package handoff and ZIP extraction."""
import hashlib,re,zipfile
from pathlib import Path
SHA256_RE=re.compile(r'^[0-9a-f]{64}$')
def sha256_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def validate_digest(value):
 value=str(value or '').lower()
 if not SHA256_RE.fullmatch(value):raise ValueError('invalid SHA-256')
 return value
def verify_package(path,expected):return Path(path).is_file() and sha256_file(path)==validate_digest(expected)
def safe_members(info_list,base,max_files=10000,max_uncompressed=2*1024*1024*1024):
 base=Path(base).resolve();seen=set();total=0;out=[]
 if len(info_list)>max_files:raise ValueError('too many ZIP members')
 for info in info_list:
  name=info.filename
  if not name or '\x00' in name or '\\' in name:raise ValueError('invalid ZIP member name')
  target=(base/name).resolve()
  if target!=base and base not in target.parents:raise ValueError('unsafe ZIP member path')
  rel=target.relative_to(base).as_posix().casefold()
  if rel in seen:raise ValueError('duplicate ZIP member path')
  seen.add(rel);total+=int(info.file_size)
  if total>max_uncompressed:raise ValueError('ZIP payload too large')
  mode=info.external_attr>>16
  if not info.is_dir() and mode and (mode&0o170000)==0o120000:raise ValueError('symbolic links are not allowed')
  out.append((info,target))
 return out
def extract_verified_zip(package,destination,expected_sha256):
 package=Path(package).resolve();destination=Path(destination).resolve()
 if not verify_package(package,expected_sha256):raise ValueError('package SHA-256 mismatch before extraction')
 destination.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(package) as archive:
  members=safe_members(archive.infolist(),destination)
  for info,target in members:
   if info.is_dir():target.mkdir(parents=True,exist_ok=True);continue
   target.parent.mkdir(parents=True,exist_ok=True)
   with archive.open(info) as source,target.open('wb') as output:
    while True:
     chunk=source.read(1024*1024)
     if not chunk:break
     output.write(chunk)
 return True
