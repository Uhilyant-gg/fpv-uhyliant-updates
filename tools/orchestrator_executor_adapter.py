"""Transport-neutral adapter for the bounded untrusted executor contract."""

from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from orchestrator_executor import ExecutorRequest, ExecutorResult, validate_result
from orchestrator_v2 import State

REQUEST_SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1


def _digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_request(
    *, story_id: str, baseline_sha: str, state: str, objective: str, max_steps: int, allowed_outputs: list[str]
) -> dict:
    request = ExecutorRequest(story_id, baseline_sha, State(state), objective, max_steps, tuple(allowed_outputs))
    request.validate()
    body = {
        "schemaVersion": REQUEST_SCHEMA_VERSION,
        "storyId": request.story_id,
        "baselineSha": request.baseline_sha,
        "state": request.state.value,
        "objective": request.objective,
        "maxSteps": request.max_steps,
        "allowedOutputs": list(request.allowed_outputs),
    }
    return {**body, "requestDigest": _digest(body)}


def parse_result(request_payload: dict, result_payload: dict) -> tuple[ExecutorResult, str]:
    required_request = {
        "schemaVersion",
        "storyId",
        "baselineSha",
        "state",
        "objective",
        "maxSteps",
        "allowedOutputs",
        "requestDigest",
    }
    required_result = {
        "schemaVersion",
        "requestDigest",
        "storyId",
        "baselineSha",
        "stepsUsed",
        "outputType",
        "payload",
        "stopReason",
    }
    if set(request_payload) != required_request or set(result_payload) != required_result:
        raise ValueError("executor envelope fields must exactly match schema")
    body = {k: request_payload[k] for k in required_request if k != "requestDigest"}
    if request_payload["schemaVersion"] != REQUEST_SCHEMA_VERSION or request_payload["requestDigest"] != _digest(body):
        raise ValueError("invalid executor request digest")
    if (
        result_payload["schemaVersion"] != RESULT_SCHEMA_VERSION
        or result_payload["requestDigest"] != request_payload["requestDigest"]
    ):
        raise ValueError("executor result not bound to request")
    request = ExecutorRequest(
        request_payload["storyId"],
        request_payload["baselineSha"],
        State(request_payload["state"]),
        request_payload["objective"],
        request_payload["maxSteps"],
        tuple(request_payload["allowedOutputs"]),
    )
    result = ExecutorResult(
        result_payload["storyId"],
        result_payload["baselineSha"],
        result_payload["stepsUsed"],
        result_payload["outputType"],
        result_payload["payload"],
        result_payload["stopReason"],
    )
    return result, validate_result(request, result)


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build-request")
    b.add_argument("--story-id", required=True)
    b.add_argument("--baseline-sha", required=True)
    b.add_argument("--state", required=True)
    b.add_argument("--objective", required=True)
    b.add_argument("--max-steps", required=True, type=int)
    b.add_argument("--allowed-output", action="append", required=True)
    b.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("validate-result")
    v.add_argument("--request", type=Path, required=True)
    v.add_argument("--result", type=Path, required=True)
    a = p.parse_args()
    try:
        if a.command == "build-request":
            payload = build_request(
                story_id=a.story_id,
                baseline_sha=a.baseline_sha,
                state=a.state,
                objective=a.objective,
                max_steps=a.max_steps,
                allowed_outputs=a.allowed_output,
            )
            a.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": "READY", "requestDigest": payload["requestDigest"]}, sort_keys=True))
            return 0
        result, status = parse_result(
            json.loads(a.request.read_text(encoding="utf-8")), json.loads(a.result.read_text(encoding="utf-8"))
        )
        print(
            json.dumps({"status": status, "storyId": result.story_id, "outputType": result.output_type}, sort_keys=True)
        )
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"status": "STATE_INCONSISTENT", "reasonCode": "invalid-executor-envelope", "summary": str(exc)},
                sort_keys=True,
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
