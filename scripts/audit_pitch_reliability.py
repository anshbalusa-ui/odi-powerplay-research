#!/usr/bin/env python3
"""Validate independent pitch coding and report categorical agreement."""

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
    pitch_intercoder_reliability,
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
    parser.add_argument("--reference-input", type=Path, required=True)
    parser.add_argument("--recoded-input", type=Path, required=True)
    parser.add_argument(
        "--innings-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument("--match-start-input", type=Path, required=True)
    parser.add_argument("--minimum-double-coded-fraction", type=float, default=0.2)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reliability.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reliability_validation_issues.csv",
    )
    args = parser.parse_args()

    reference_rows = read_csv(args.reference_input)
    recoded_rows = read_csv(args.recoded_input)
    innings_rows = read_csv(args.innings_input)
    eligible_ids = {row["match_id"] for row in innings_rows}
    start_time_rows = read_csv(args.match_start_input)
    start_time_issues = validate_match_start_rows(
        start_time_rows,
        eligible_rows=build_match_start_queue(innings_rows),
    )
    match_starts = verified_match_start_map(start_time_rows) if not start_time_issues else {}

    issues: list[dict[str, str]] = [
        {"coding_set": "match_start", **issue} for issue in start_time_issues
    ]
    for coding_set, rows in (
        ("reference", reference_rows),
        ("recoded", recoded_rows),
    ):
        issues.extend(
            {"coding_set": coding_set, **issue}
            for issue in validate_pitch_rows(
                rows,
                eligible_match_ids=eligible_ids,
                match_start_by_id=match_starts,
            )
        )

    if issues:
        args.issues_output.parent.mkdir(parents=True, exist_ok=True)
        with args.issues_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(issues[0]))
            writer.writeheader()
            writer.writerows(issues)
        report = {
            "validation_issue_count": len(issues),
            "validation_issues_by_coding_set": dict(
                sorted(Counter(issue["coding_set"] for issue in issues).items())
            ),
            "validation_issues_by_field": dict(
                sorted(Counter(issue["field"] for issue in issues).items())
            ),
            "issues_output": str(args.issues_output),
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    if args.issues_output.exists():
        args.issues_output.unlink()
    summary = pitch_intercoder_reliability(
        reference_rows,
        recoded_rows,
        minimum_double_coded_fraction=args.minimum_double_coded_fraction,
    )
    summary["validation_issue_count"] = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(not summary["meets_minimum_double_coding_target"])


if __name__ == "__main__":
    raise SystemExit(main())
