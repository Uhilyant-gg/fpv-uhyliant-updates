def install_decision(busy, guard_ok, install_ready):
    if busy:
        return 'busy'
    if not guard_ok:
        return 'blocked'
    if not install_ready:
        return 'unavailable'
    return 'handoff'


def helper_args(helper, root, ready, pid):
    if not isinstance(ready, dict) or set(ready) != {'version', 'package', 'sha256'}:
        raise RuntimeError('Некоректний стан пакета для запуску updater')
    if type(pid) is not int or pid <= 0:
        raise RuntimeError('Некоректний PID для запуску updater')
    return [str(helper), '--root', str(root), '--package', ready['package'], '--version', ready['version'], '--sha256', ready['sha256'], '--wait-pid', str(pid)]
