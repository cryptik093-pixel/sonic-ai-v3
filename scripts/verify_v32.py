"""Verify the integrated V3.2 source in disposable storage, without provider calls.

Run from any directory: python scripts/verify_v32.py --output artifacts/v3.2/run.json
This does not certify workstation recovery, a native build, FL Studio or sales.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def isolated_environment(parent: dict[str, str], storage: Path) -> dict[str, str]:
    """Never inherit a user's Sonic database location, token or provider config."""
    env = {key: value for key, value in parent.items()
           if not key.startswith("SONIC_") and key not in {"OPENAI_API_KEY", "PYTHONPATH"}}
    env.update(PYTHON_DOTENV_DISABLED="1", PYTHONPATH=str(ROOT),
               SONIC_DATA_DIR=str(storage), SONIC_DB_PATH=str(storage / "app.db"),
               SONIC_EVENT_DB=str(storage / "events.db"),
               SONIC_INTEGRITY_DB=str(storage / "integrity.db"))
    return env


def source_identity() -> dict:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, timeout=15)
    try:
        diff = git("diff", "HEAD", "--", ".")
        status = git("status", "--porcelain=v1", "--untracked-files=normal")
        return {"head": git("rev-parse", "HEAD").decode().strip(),
                "branch": git("branch", "--show-current").decode().strip(),
                "dirty": bool(status), "tracked_diff_sha256": hashlib.sha256(diff).hexdigest()}
    except (OSError, subprocess.SubprocessError):
        return {"head": None, "status": "unavailable"}


def run_check(name: str, command: list[str], env: dict, logs: Path, timeout: int) -> dict:
    started = time.monotonic()
    log = logs / (name + ".log")
    with log.open("x", encoding="utf-8") as stream:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            code, error = result.returncode, None
        except subprocess.TimeoutExpired:
            code, error = None, "timeout"
        except OSError as exc:
            code, error = None, type(exc).__name__
    return {"name": name, "command": command, "passed": code == 0,
            "exit_code": code, "error": error,
            "seconds": round(time.monotonic() - started, 3), "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    logs = output.with_name(output.stem + "-logs")
    if output.exists() or logs.exists():
        parser.error("Choose a new output filename; previous verification evidence is preserved.")
    output.parent.mkdir(parents=True, exist_ok=True)
    logs.mkdir()
    report = {"schema": "sonic.v3.2.source-verification/1", "target": "3.2",
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "source": source_identity(), "platform": platform.system(),
              "python": platform.python_version(), "storage": "disposable",
              "source_checks_passed": False, "upgrade_complete": False,
              "unverified": ["Windows working-tree preservation and reconciliation",
                             "native Windows packaging", "FL Studio save/reopen and audio",
                             "VST3 state roundtrip", "live Shopify and paid sales"],
              "checks": []}
    with tempfile.TemporaryDirectory(prefix="sonic-v32-verify-") as temp:
        env = isolated_environment(dict(os.environ), Path(temp))
        steps = [
            ("foundation", ["node", "scripts/validate-v3-foundation.mjs"], 30),
            ("api-and-legacy", [sys.executable, "-m", "pytest", "apps/api", "-q", "--disable-warnings"], 180),
            ("desktop-http", [sys.executable, "apps/desktop/launcher.py", "--smoke-test", str(logs / "desktop-smoke.json")], 90),
        ]
        for name, command, timeout in steps:
            check = run_check(name, command, env, logs, timeout)
            if name == "desktop-http" and check["passed"]:
                try:
                    proof = json.loads((logs / "desktop-smoke.json").read_text(encoding="utf-8"))
                    check["passed"] = proof.get("passed") is True
                    check["proof"] = proof
                except (ValueError, OSError):
                    check.update(passed=False, error="missing_or_invalid_smoke_proof")
            report["checks"].append(check)
            print(f"{name}: {'PASS' if check['passed'] else 'FAIL'}", flush=True)
            if not check["passed"]:
                break
    report["source_checks_passed"] = len(report["checks"]) == 3 and all(c["passed"] for c in report["checks"])
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(f"Evidence: {output}", flush=True)
    return 0 if report["source_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
