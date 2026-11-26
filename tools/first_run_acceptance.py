#!/usr/bin/env python3
"""Run the deterministic first-run acceptance contract and emit JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from first_run_acceptance import evaluate_first_run


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path, help="JSON snapshot of the normal first-run presentation state")
    parser.add_argument("--elapsed-ms", required=True, type=int)
    parser.add_argument("--deadline-ms", type=int, default=10_000)
    args = parser.parse_args(argv)
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    result = evaluate_first_run(snapshot, elapsed_ms=args.elapsed_ms, deadline_ms=args.deadline_ms).as_dict()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
