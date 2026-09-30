#!/usr/bin/env python3
"""Run the repository's CI commands locally and record their exit evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/ci_clean_run.json",
    )
    args = parser.parse_args()
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-m", "compileall", "-q", "src", "scripts"],
    ]
    evidence: list[dict[str, object]] = []
    for command in commands:
        started = time.monotonic()
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        evidence.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "duration_seconds": round(time.monotonic() - started, 6),
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            }
        )
        if completed.returncode != 0:
            break
    result = {
        "status": "pass" if all(item["returncode"] == 0 for item in evidence) and len(evidence) == len(commands) else "fail",
        "workflow_commands": evidence,
        "workflow_file": ".github/workflows/tests.yml",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
