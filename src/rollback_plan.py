def rollback_preconditions(current_exists, rollback_exists):
    if not rollback_exists:
        return 'missing-rollback'
    return 'replace-current' if current_exists else 'restore-rollback'


def rolled_back_state(state, timestamp):
    result = dict(state) if isinstance(state, dict) else {}
    failed_version = result.get('current')
    restored_version = result.get('lastGood')
    restored_sha256 = result.get('lastGoodPackageSha256')
    result['pendingStartup'] = False
    result['rollbackAt'] = timestamp
    if failed_version:
        result['failedVersion'] = failed_version
    if restored_version:
        result['current'] = restored_version
    if restored_sha256:
        result['packageSha256'] = restored_sha256
    return result
