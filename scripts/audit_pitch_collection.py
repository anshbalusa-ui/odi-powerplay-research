#!/usr/bin/env python3
"""Validate manual pitch coding and summarize source coverage."""

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
    PITCH_COLLECTION_STATUS_FIELDS,
    build_pitch_collection_queue,
    build_pitch_collection_status,
    pitch_coverage_summary,
    validate_pitch_rows,
)
from odi_powerplay.start_times import (  # noqa: E402
    build_match_start_queue,
    validate_match_start_rows,
    verified_match_start_map,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitch-input", type=Path, required=True)
    parser.add_argument(
        "--innings-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument("--match-start-input", type=Path)
    parser.add_argument(
        "--set-aside-input",
        type=Path,
        default=ROOT / "data/manual/pitch_set_aside.csv",
    )
    parser.add_argument(
        "--status-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_collection_status.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_coverage_audit.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_validation_issues.csv",
    )
    args = parser.parse_args()

    pitch_rows = read_csv(args.pitch_input)
    innings_rows = read_csv(args.innings_input)
    eligible_ids = {row["match_id"] for row in innings_rows}
    set_aside_rows = read_csv(args.set_aside_input)
    match_starts = None
    start_time_issues: list[dict[str, str]] = []
    if args.match_start_input:
        start_time_rows = read_csv(args.match_start_input)
        start_time_issues = validate_match_start_rows(
            start_time_rows,
            eligible_rows=build_match_start_queue(innings_rows),
        )
        match_starts = verified_match_start_map(start_time_rows) if not start_time_issues else {}

    issues = validate_pitch_rows(
        pitch_rows,
        eligible_match_ids=eligible_ids,
        match_start_by_id=match_starts,
    )
    issues.extend(start_time_issues)
    summary = pitch_coverage_summary(pitch_rows, eligible_match_count=len(eligible_ids))
    summary["validation_issue_count"] = len(issues)
    summary["validation_issues_by_field"] = dict(
        sorted(Counter(issue["field"] for issue in issues).items())
    )
    collection_status = build_pitch_collection_status(
        build_pitch_collection_queue(innings_rows),
        pitch_rows,
        set_aside_rows,
    )
    summary["collection_status_counts"] = dict(
        sorted(Counter(row["collection_status"] for row in collection_status).items())
    )

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.status_output.parent.mkdir(parents=True, exist_ok=True)
    with args.status_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PITCH_COLLECTION_STATUS_FIELDS)
        writer.writeheader()
        writer.writerows(collection_status)
    if issues:
        args.issues_output.parent.mkdir(parents=True, exist_ok=True)
        with args.issues_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(issues[0]))
            writer.writeheader()
            writer.writerows(issues)
    elif args.issues_output.exists():
        args.issues_output.unlink()

    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
