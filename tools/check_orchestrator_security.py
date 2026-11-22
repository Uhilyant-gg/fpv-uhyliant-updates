"""Tiny executable Phase-1 BDD gate without adding a BDD dependency."""
from pathlib import Path
import unittest

REQUIRED_TAGS={"@security","@P0","@state-machine","@stale-execution","@merge-gate","@hardware","@physical-boundary","@repair-loop","@concurrency","@provider-failure","@recovery","@fail-closed","@adversarial","@level2"}


def main():
    feature=Path(__file__).resolve().parents[1]/"features"/"orchestrator_v2_security.feature"
    text=feature.read_text(encoding="utf-8")
    missing=sorted(tag for tag in REQUIRED_TAGS if tag not in text)
    if missing:
        raise SystemExit("missing security tags: "+", ".join(missing))
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_orchestrator_v2.py")
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
