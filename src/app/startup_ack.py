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
