def rollback_preconditions(current_exists, rollback_exists):
    if not rollback_exists:
        return 'missing-rollback'
    return 'replace-current' if current_exists else 'restore-rollback'


def rolled_back_state(state, timestamp):
    result = dict(state) if isinstance(state, dict) else {}
    result['pendingStartup'] = False
    result['rollbackAt'] = timestamp
    return result
