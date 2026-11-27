import hashlib,os,shutil
from pathlib import Path


def install_decision(busy, guard_ok, install_ready):
    if busy:
        return 'busy'
    if not guard_ok:
        return 'blocked'
    if not install_ready:
        return 'unavailable'
    return 'handoff'


def _sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def stage_ready_package(root, ready):
    if not isinstance(ready,dict) or set(ready)!={'version','package','sha256'}:raise RuntimeError('Некоректний стан пакета для staging')
    source=Path(ready['package']).resolve();expected=str(ready['sha256']).lower();install_root=Path(root).resolve()
    if not source.is_file() or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or _sha256(source)!=expected:raise RuntimeError('Пакет не пройшов перевірку перед staging')
    updates=install_root/'updates';updates.mkdir(parents=True,exist_ok=True);target=updates/source.name;tmp=target.with_suffix(target.suffix+'.part')
    try:
        tmp.unlink(missing_ok=True);shutil.copyfile(source,tmp)
        if _sha256(tmp)!=expected:raise RuntimeError('Пакет змінився під час staging')
        os.replace(tmp,target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return {'version':ready['version'],'package':str(target),'sha256':expected}


def helper_args(helper, root, ready, pid):
    if not isinstance(ready, dict) or set(ready) != {'version', 'package', 'sha256'}:
        raise RuntimeError('Некоректний стан пакета для запуску updater')
    if type(pid) is not int or pid <= 0:
        raise RuntimeError('Некоректний PID для запуску updater')
    return [str(helper), '--root', str(root), '--package', ready['package'], '--version', ready['version'], '--sha256', ready['sha256'], '--wait-pid', str(pid)]
