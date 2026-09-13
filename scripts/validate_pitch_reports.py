#!/usr/bin/env python3
"""Validate local pitch-report codes against the fixed ODI cohort."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.pitch import validate_pitch_rows  # noqa: E402
from odi_powerplay.start_times import verified_match_start_map  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matches",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--pitch-registry",
        type=Path,
        default=PROJECT_ROOT / "data/manual/pitch_reports_verified.csv",
    )
    parser.add_argument(
        "--match-start-input",
        type=Path,
        default=PROJECT_ROOT / "data/manual/match_start_times_verified.csv",
    )
    parser.add_argument(
        "--validated-output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/pitch_reports_validated.csv",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=PROJECT_ROOT / "artifacts/tables/pitch_validation_issues.csv",
    )
    args = parser.parse_args()

    primary_rows = [row for row in read_csv(args.matches) if int(row["innings_number"]) == 1]
    eligible_match_ids = {row["match_id"] for row in primary_rows}
    pitch_rows = read_csv(args.pitch_registry)
    match_starts = verified_match_start_map(read_csv(args.match_start_input))
    issues = validate_pitch_rows(
        pitch_rows,
        eligible_match_ids=eligible_match_ids,
        match_start_by_id=match_starts,
    )
    invalid_match_ids = {
        issue["cricsheet_match_id"] for issue in issues if issue["cricsheet_match_id"]
    }
    usable = [
        row
        for row in pitch_rows
        if row["pre_match_verified"] == "1" and row["cricsheet_match_id"] not in invalid_match_ids
    ]

    pitch_fieldnames = list(pitch_rows[0]) if pitch_rows else []
    write_csv(usable, args.validated_output, pitch_fieldnames)
    issue_fieldnames = ["cricsheet_match_id", "field", "message"]
    write_csv(issues, args.issues_output, issue_fieldnames)

    exclusions = Counter(row["exclusion_reason"] for row in pitch_rows if row["exclusion_reason"])
    errors = issues
    summary = {
        "registry_rows": len(pitch_rows),
        "usable_pitch_rows": len(usable),
        "excluded_or_no_evidence_rows": sum(exclusions.values()),
        "errors": len(errors),
        "exclusion_reasons": dict(sorted(exclusions.items())),
        "validated_output": str(args.validated_output.relative_to(PROJECT_ROOT)),
        "issues_output": str(args.issues_output.relative_to(PROJECT_ROOT)),
    }
    print(json.dumps(summary, indent=2))
    if errors:
        raise SystemExit("Pitch validation found one or more errors")


if __name__ == "__main__":
    main()
