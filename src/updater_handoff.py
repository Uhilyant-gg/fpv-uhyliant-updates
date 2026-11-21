import re
from pathlib import Path

SHA_RE = re.compile(r'^[0-9a-fA-F]{64}$')


def valid_handoff(root, package, version, sha256, wait_pid):
    try:
        install_root = Path(root).resolve()
        package_path = Path(package).resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    return bool(
        version
        and version == Path(version).name
        and SHA_RE.fullmatch(sha256 or '')
        and type(wait_pid) is int
        and wait_pid > 0
        and package_path.is_file()
        and package_path.parent == install_root / 'updates'
    )
