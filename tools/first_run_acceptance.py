#!/usr/bin/env python3
"""Run the deterministic first-run acceptance contract and emit JSON."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "src" / "app" / "first_run_acceptance.py"


def _load_contract():
    """Load the app contract under a unique name to avoid tools module shadowing."""
    spec = importlib.util.spec_from_file_location("fpv_first_run_acceptance_contract", CONTRACT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("first-run acceptance contract is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path, help="JSON snapshot of the normal first-run presentation state")
    parser.add_argument("--elapsed-ms", required=True, type=int)
    parser.add_argument("--deadline-ms", type=int, default=10_000)
    args = parser.parse_args(argv)
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    contract = _load_contract()
    result = contract.evaluate_first_run(
        snapshot, elapsed_ms=args.elapsed_ms, deadline_ms=args.deadline_ms
    ).as_dict()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
