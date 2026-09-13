#!/usr/bin/env python3
"""Audit strict-codebook review state against the verified pitch release."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (  # noqa: E402
    apply_pitch_reaudit,
    validate_pitch_reaudit_registry,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pitch-input",
        type=Path,
        default=ROOT / "data/manual/pitch_reports_verified.csv",
    )
    parser.add_argument(
        "--registry-input",
        type=Path,
        default=ROOT / "data/manual/pitch_code_reaudit.csv",
    )
    parser.add_argument("--legacy-count", type=int, default=228)
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reaudit_status.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reaudit_issues.csv",
    )
    args = parser.parse_args()

    pitch_rows = read_csv(args.pitch_input)
    registry = read_csv(args.registry_input)
    issues = validate_pitch_reaudit_registry(
        registry,
        pitch_rows,
        legacy_count=args.legacy_count,
    )
    statuses = Counter(str(row.get("reaudit_status", "")).strip() for row in registry)
    standards = Counter(str(row.get("coding_standard", "")).strip() for row in registry)
    compliant_count = 0
    if not issues:
        compliant_count = len(
            apply_pitch_reaudit(
                pitch_rows,
                registry,
                legacy_count=args.legacy_count,
            )
        )
    summary = {
        "pitch_release_rows": len(pitch_rows),
        "registry_rows": len(registry),
        "legacy_count": args.legacy_count,
        "coding_standards": dict(sorted(standards.items())),
        "reaudit_statuses": dict(sorted(statuses.items())),
        "compliant_rows": compliant_count,
        "legacy_reaudit_complete": (
            not issues
            and statuses["pending"] == 0
            and sum(
                statuses[name]
                for name in ("passed_unchanged", "passed_revised", "source_unavailable")
            )
            == args.legacy_count
        ),
        "validation_issue_count": len(issues),
        "validation_issues_by_field": dict(
            sorted(Counter(issue["field"] for issue in issues).items())
        ),
    }

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if issues:
        args.issues_output.parent.mkdir(parents=True, exist_ok=True)
        with args.issues_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(issues[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(issues)
    elif args.issues_output.exists():
        args.issues_output.unlink()

    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
