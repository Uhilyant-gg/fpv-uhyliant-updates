import json,re,time,uuid
from copy import deepcopy

SECRET_KEYS={'password','passwd','secret','token','privatekey','private_key','apikey','api_key','authorization','credential','credentials','sshkey','ssh_key','signingkey','signing_key'}
_SECRET_KEY_PARTS=('password','passwd','secret','token','privatekey','apikey','authorization','credential','sshkey','signingkey')

def _secret_key(key):
    normalized=re.sub(r'[^a-z0-9]','',str(key).lower())
    return normalized in {re.sub(r'[^a-z0-9]','',k) for k in SECRET_KEYS} or any(part in normalized for part in _SECRET_KEY_PARTS)

def _sanitize(value):
    if isinstance(value,dict):
        out={}
        for key,item in value.items():
            name=str(key)
            out[name]='[redacted]' if _secret_key(name) else _sanitize(item)
        return out
    if isinstance(value,list):return [_sanitize(v) for v in value]
    if isinstance(value,tuple):return [_sanitize(v) for v in value]
    return value

def diagnostic_bundle(version,build=None,devices=None,network=None,video=None,protocols=None,updater=None,events=None,now=None,correlation_id=None):
    payload={
        'schemaVersion':1,
        'correlationId':correlation_id or uuid.uuid4().hex,
        'generatedAt':int(time.time() if now is None else now),
        'application':{'version':version or None,'build':build or None},
        'devices':deepcopy(devices) if devices is not None else [],
        'network':deepcopy(network) if network is not None else {},
        'video':deepcopy(video) if video is not None else {},
        'protocols':deepcopy(protocols) if protocols is not None else {},
        'updater':deepcopy(updater) if updater is not None else {},
        'events':list(events or [])[-100:],
    }
    return _sanitize(payload)

def export_bundle(path,bundle):
    text=json.dumps(_sanitize(bundle),ensure_ascii=False,sort_keys=True,indent=2)
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(path);return path
