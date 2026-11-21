def pending_ack(payload, token, version):
    return bool(
        isinstance(payload, dict)
        and set(payload) == {'status', 'token', 'version'}
        and payload.get('status') == 'ok'
        and isinstance(token, str)
        and bool(token)
        and payload.get('token') == token
        and isinstance(version, str)
        and bool(version)
        and payload.get('version') == version
    )


def startup_verdict(payload, token, version, process_running, timed_out):
    if pending_ack(payload, token, version):
        return 'accept'
    if not process_running:
        return 'rollback-process-exited'
    if timed_out:
        return 'rollback-timeout'
    return 'wait'
