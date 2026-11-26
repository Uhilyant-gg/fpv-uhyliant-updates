#!/usr/bin/env python3
"""One-command local preflight and setup for the FPV Uhyliant workspace."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FILES = (
    "PRODUCT_UX.md",
    "PROJECT_STATE.md",
    "PROJECT_STATE.json",
    "DELIVERY_ROADMAP.md",
    "DEVELOPMENT_GUIDE.md",
)


def find_compatible_python() -> tuple[Path | None, str]:
    if os.name == "nt":
        for minor in (13, 12, 11, 10):
            try:
                result = subprocess.run(
                    ["py", f"-3.{minor}", "-c", "import sys; print(sys.executable)"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=20,
                )
                if result.returncode == 0:
                    executable = Path(result.stdout.strip())
                    if executable.is_file():
                        return executable, f"3.{minor}"
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                pass
        return None, "Python 3.10-3.13 required; compatible interpreter not found"

    if sys.version_info >= (3, 10) and sys.version_info < (3, 14):
        return Path(sys.executable), ".".join(map(str, sys.version_info[:3]))
    return None, "Python 3.10-3.13 required; compatible interpreter not found"


def preflight(root: Path) -> dict:
    root = root.resolve()
    missing = [name for name in CANONICAL_FILES if not (root / name).is_file()]
    requirements = root / "src" / "requirements.txt"
    launcher = root / "src" / "launcher.py"
    compatible_python, python_detail = find_compatible_python()
    checks = [
        {"name": "python", "ok": compatible_python is not None, "detail": python_detail},
        {"name": "canonical-files", "ok": not missing, "detail": "present" if not missing else "missing: " + ", ".join(missing)},
        {"name": "requirements", "ok": requirements.is_file(), "detail": str(requirements)},
        {"name": "launcher", "ok": launcher.is_file(), "detail": str(launcher)},
        {"name": "git-worktree", "ok": (root / ".git").exists() or (root / ".git").is_file(), "detail": str(root)},
    ]
    ok = all(check["ok"] for check in checks)
    return {"ok": ok, "checks": checks}


def run_command(name: str, command: Iterable[str], cwd: Path, timeout: int = 300) -> dict:
    try:
        result = subprocess.run(
            list(command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "ok": False, "detail": "Перевищено час очікування.", "exitCode": None}
    except Exception:
        return {"name": name, "ok": False, "detail": "Не вдалося запустити перевірку.", "exitCode": None}
    lines = "\n".join(result.stdout.splitlines()[-20:])
    return {
        "name": name,
        "ok": result.returncode == 0,
        "detail": lines[-3000:] if lines else ("Готово." if result.returncode == 0 else "Перевірка завершилася з помилкою."),
        "exitCode": result.returncode,
    }


def bootstrap(root: Path, *, install: bool = True, smoke: bool = True) -> dict:
    root = root.resolve()
    result = {"schemaVersion": 1, "status": "BLOCKED", "stage": "preflight", "reasonCode": "project-bootstrap-blocked", "summary": "", "checks": []}
    pre = preflight(root)
    result["checks"].append({"name": "preflight", "ok": pre["ok"], "detail": pre["checks"]})
    if not pre["ok"]:
        result["summary"] = "Проєкт не готовий до автоматичного налаштування."
        result["reasonCode"] = "preflight-failed"
        return result

    compatible_python, python_detail = find_compatible_python()
    if compatible_python is None:
        result["summary"] = "Потрібно встановити сумісний Python 3.10-3.13."
        result["reasonCode"] = "compatible-python-required"
        return result

    venv_dir = root / ".venv"
    venv_python = venv_dir / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if not venv_python.is_file():
        result["stage"] = "environment"
        check = run_command("create-virtual-environment", [str(compatible_python), "-m", "venv", str(venv_dir)], root)
        result["checks"].append(check)
        if not check["ok"]:
            result["summary"] = "Не вдалося підготувати локальне середовище."
            result["reasonCode"] = "environment-failed"
            return result

    if install:
        result["stage"] = "dependencies"
        check = run_command(
            "install-dependencies",
            [str(venv_python), "-m", "pip", "install", "-r", str(root / "src" / "requirements.txt")],
            root,
            timeout=600,
        )
        result["checks"].append(check)
        if not check["ok"]:
            result["summary"] = "Не вдалося встановити залежності."
            result["reasonCode"] = "dependencies-failed"
            return result

    result["stage"] = "compile"
    check = run_command("compile", [str(venv_python), "-m", "compileall", "-q", "-f", "src", "tools"], root)
    result["checks"].append(check)
    if not check["ok"]:
        result["summary"] = "Проєкт не проходить перевірку Python-коду."
        result["reasonCode"] = "compile-failed"
        return result

    if smoke:
        result["stage"] = "launch-smoke"
        marker = root / ".bootstrap-smoke.json"
        marker.unlink(missing_ok=True)
        check = run_command(
            "qml-smoke",
            [str(venv_python), "main.py", "--smoke-test", "--smoke-marker", str(marker)],
            root / "src" / "app",
            timeout=300,
        )
        result["checks"].append(check)
        if not check["ok"]:
            result["summary"] = "Програму встановлено, але запуск перевірки не пройдено."
            result["reasonCode"] = "launch-smoke-failed"
            return result
        if not marker.is_file():
            result["summary"] = "Перевірка запуску не дала підтвердження."
            result["reasonCode"] = "launch-smoke-evidence-missing"
            result["checks"].append({"name": "smoke-evidence", "ok": False, "detail": "Файл підтвердження запуску не створено."})
            return result
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = {}
        evidence_ok = payload.get("status") == "ok"
        result["checks"].append({"name": "smoke-evidence", "ok": evidence_ok, "detail": "present" if evidence_ok else "invalid"})
        if not evidence_ok:
            result["summary"] = "Підтвердження запуску містить невірний стан."
            result["reasonCode"] = "launch-smoke-evidence-invalid"
            return result

    result["status"] = "READY"
    result["stage"] = "ready"
    result["reasonCode"] = "project-bootstrap-ready"
    result["summary"] = "Проєкт готовий до локального запуску."
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare this FPV Uhyliant workspace.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--json", action="store_true", dest="machine_json")
    args = parser.parse_args()

    result = bootstrap(Path(args.root), install=not args.skip_install, smoke=not args.skip_smoke)
    if args.machine_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(result["summary"])
        for check in result["checks"]:
            name = check["name"]
            ok = "ГОТОВО" if check["ok"] else "ПОТРІБНА ДІЯ"
            print(f"- {name}: {ok}")
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
