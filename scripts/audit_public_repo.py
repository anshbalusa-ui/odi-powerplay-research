#!/usr/bin/env python3
"""Audit the tracked repository surface for reproducibility and public release risks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "AGENTS.md",
    "pyproject.toml",
    ".github/workflows/tests.yml",
    "config/study.yaml",
    "config/modeling.json",
    "scripts/reproduce.py",
)
FORBIDDEN_TRACKED_PREFIXES = (
    "data/raw/",
    "data/interim/",
    "data/processed/",
    "artifacts/models/",
    "artifacts/tables/",
)
FORBIDDEN_WORKING_FILES = {
    "data/manual/pitch_reports.csv",
    "data/manual/pitch_reports_double_coded.csv",
    "data/manual/match_start_times.csv",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/public_repo_readiness.json",
    )
    args = parser.parse_args()

    paths = tracked_paths()
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    tracked_set = set(paths)
    for required in REQUIRED_FILES:
        if required not in tracked_set:
            issues.append({"check": "required_file", "path": required, "message": "missing"})

    forbidden_data = [
        path
        for path in paths
        if path.startswith(FORBIDDEN_TRACKED_PREFIXES)
        and not path.endswith(".gitkeep")
    ]
    for path in forbidden_data:
        issues.append(
            {
                "check": "derived_data_tracking",
                "path": path,
                "message": "raw/derived data or generated artifact is tracked",
            }
        )
    for path in sorted(FORBIDDEN_WORKING_FILES & tracked_set):
        issues.append(
            {
                "check": "working_file_tracking",
                "path": path,
                "message": "local source-derived working file is tracked",
            }
        )

    secret_hits: list[str] = []
    for relative in paths:
        path = ROOT / relative
        if path.stat().st_size > 5_000_000:
            warnings.append(
                {
                    "check": "tracked_file_size",
                    "path": relative,
                    "message": "tracked file exceeds 5 MB",
                }
            )
        if path.suffix.lower() not in {".py", ".yaml", ".yml", ".json", ".toml", ".md", ".csv", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                secret_hits.append(relative)
                break
    for path in sorted(set(secret_hits)):
        issues.append(
            {
                "check": "credential_scan",
                "path": path,
                "message": "credential-like token pattern detected",
            }
        )

    if "data/manual/pitch_reports_verified.csv" in tracked_set:
        warnings.append(
            {
                "check": "source_rights_review",
                "path": "data/manual/pitch_reports_verified.csv",
                "message": "public release still requires source-license/terms review",
            }
        )
    if "data/manual/pitch_code_reaudit.csv" in tracked_set:
        warnings.append(
            {
                "check": "source_rights_review",
                "path": "data/manual/pitch_code_reaudit.csv",
                "message": "public release still requires source-license/terms review",
            }
        )

    result = {
        "status": "pass_with_warnings" if not issues else "blocked",
        "tracked_file_count": len(paths),
        "required_files_present": not any(issue["check"] == "required_file" for issue in issues),
        "derived_data_tracked": bool(forbidden_data),
        "working_files_tracked": bool(FORBIDDEN_WORKING_FILES & tracked_set),
        "credential_pattern_hits": sorted(set(secret_hits)),
        "issues": issues,
        "warnings": warnings,
        "branch_changes_are_not_release_evidence": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
