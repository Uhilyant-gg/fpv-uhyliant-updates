"""Executable Phase-1 security policy gate without adding a BDD dependency."""

from pathlib import Path
import unittest

REQUIRED_TAGS = {
    "@security",
    "@P0",
    "@state-machine",
    "@stale-execution",
    "@merge-gate",
    "@protected-files",
    "@ci-integrity",
    "@generated",
    "@supply-chain",
    "@hardware",
    "@physical-boundary",
    "@repair-loop",
    "@concurrency",
    "@provider-failure",
    "@recovery",
    "@audit",
    "@fail-closed",
    "@adversarial",
    "@input-validation",
    "@level2",
}


def main():
    feature = Path(__file__).resolve().parents[1] / "features" / "orchestrator_v2_security.feature"
    text = feature.read_text(encoding="utf-8")
    missing = sorted(tag for tag in REQUIRED_TAGS if tag not in text)
    if missing:
        raise SystemExit("missing security tags: " + ", ".join(missing))
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_orchestrator*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
