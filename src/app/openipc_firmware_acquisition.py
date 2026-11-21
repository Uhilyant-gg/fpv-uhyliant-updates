"""Fail-closed resolver for the official OpenIPC firmware manifest."""
import hashlib,json
from pathlib import Path
from urllib.parse import urlparse
OFFICIAL_MANIFEST_URL='https://<scrubbed-url-domain>/firmware/manifest.json'
OFFICIAL_DOWNLOAD_HOSTS=('openipc.org','openipc.github.io')
MAX_MANIFEST_BYTES=4*1024*1024
MAX_FIRMWARE_BYTES=64*1024*1024

def _text(value):return str(value).strip() if isinstance(value,(str,int)) else ''
def _sha(value):
 value=_text(value).lower();return value if len(value)==64 and all(c in '0123456789abcdef' for c in value) else ''
def _official_url(value):
 try:p=urlparse(_text(value));return p.scheme=='https' and p.hostname in OFFICIAL_DOWNLOAD_HOSTS and not p.username and not p.password and bool(p.path)
 except ValueError:return False
def _entries(payload):
 if isinstance(payload,list):return payload
 if not isinstance(payload,dict):return []
 for key in ('firmwares','builds','images','artifacts'):
  if isinstance(payload.get(key),list):return payload[key]
 return []
def _field(item,*names):
 for name in names:
  value=item.get(name) if isinstance(item,dict) else None
  if value not in (None,''):return value
 return ''

def parse_catalog(raw):
 if isinstance(raw,str):raw=raw.encode('utf-8')
 if not isinstance(raw,(bytes,bytearray)) or not raw or len(raw)>MAX_MANIFEST_BYTES:return []
 try:payload=json.loads(bytes(raw).decode('utf-8'))
 except (UnicodeError,json.JSONDecodeError):return []
 result=[]
 for item in _entries(payload):
  if not isinstance(item,dict):continue
  platform=_text(_field(item,'platform','soc','chip')).lower();sensor=_text(_field(item,'sensor')).lower();variant=_text(_field(item,'variant','flavor')).lower();channel=_text(_field(item,'channel'));build=_text(_field(item,'build','version','release'));url=_text(_field(item,'url','download','download_url'));sha=_sha(_field(item,'sha256','sha'))
  try:size=int(_field(item,'size','bytes') or 0)
  except (TypeError,ValueError):size=0
  if platform and sensor and variant and channel and build and _official_url(url) and sha and 0<size<=MAX_FIRMWARE_BYTES:result.append({'platform':platform,'sensor':sensor,'variant':variant,'channel':channel,'build':build,'url':url,'sha256':sha,'size':size})
 return result

def resolve(catalog,platform,sensor,channel='',build='',variant=''):
 platform=_text(platform).lower();sensor=_text(sensor).lower();channel=_text(channel);build=_text(build);variant=_text(variant).lower()
 if not platform or not sensor:return {'ready':False,'reason':'Платформу або сенсор не підтверджено'}
 matches=[x for x in catalog if x.get('platform')==platform and x.get('sensor')==sensor]
 if channel:matches=[x for x in matches if x.get('channel')==channel]
 if build:matches=[x for x in matches if x.get('build')==build]
 if variant:matches=[x for x in matches if x.get('variant')==variant]
 variants=sorted({x.get('variant','') for x in matches if x.get('variant')})
 if not variant and len(variants)>1:return {'ready':False,'reason':'Варіант прошивки потрібно вибрати явно','variants':variants}
 if not build and len({x.get('build','') for x in matches})>1:return {'ready':False,'reason':'Збірку прошивки потрібно вибрати явно','builds':sorted({x.get('build','') for x in matches})}
 if len(matches)!=1:return {'ready':False,'reason':'Не знайдено однозначно сумісний образ'}
 return {'ready':True,'artifact':dict(matches[0])}

def verify_download(path,artifact):
 if not isinstance(artifact,dict):return False
 expected=_sha(artifact.get('sha256'));expected_size=artifact.get('size')
 try:expected_size=int(expected_size)
 except (TypeError,ValueError):return False
 if not expected or expected_size<=0 or expected_size>MAX_FIRMWARE_BYTES:return False
 p=Path(path);h=hashlib.sha256();size=0
 try:
  with p.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):
    size+=len(chunk)
    if size>expected_size:return False
    h.update(chunk)
 except OSError:return False
 return size==expected_size and h.hexdigest()==expected
