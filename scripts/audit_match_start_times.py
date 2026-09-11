#!/usr/bin/env python3
"""Audit manually verified match starts without requesting external sources."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.start_times import (  # noqa: E402
    build_match_start_queue,
    match_start_coverage_summary,
    validate_match_start_rows,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/manual/match_start_times_template.csv",
    )
    parser.add_argument(
        "--innings-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
        help="Primary cohort innings used to validate match identity and coverage.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/match_start_time_audit.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/match_start_time_issues.csv",
    )
    args = parser.parse_args()

    rows = read_csv(args.input)
    reference_rows = build_match_start_queue(read_csv(args.innings_input))
    issues = validate_match_start_rows(rows, eligible_rows=reference_rows)
    summary = match_start_coverage_summary(rows)
    summary["validation_issue_count"] = len(issues)
    summary["validation_issues_by_field"] = dict(
        sorted(Counter(issue["field"] for issue in issues).items())
    )
    summary["input"] = str(args.input)
    summary["innings_input"] = str(args.innings_input)
    summary["network_requests_performed"] = 0

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
