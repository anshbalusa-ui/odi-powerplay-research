#!/usr/bin/env python3
"""Independently audit the unlocked full-cohort non-pitch analysis."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.analysis_audit import audit_unlocked_model_rows  # noqa: E402


def read_without_locked_outcomes(path: Path) -> list[dict[str, str]]:
    """Read full rows only for unlocked splits; retain structure-only fields for locked rows."""

    safe_locked_fields = ("match_id", "match_date", "innings_number", "split")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        positions = {field: index for index, field in enumerate(header)}
        required = {*safe_locked_fields, "batting_team_won", "pp_runs"}
        missing = sorted(required - positions.keys())
        if missing:
            raise ValueError(f"Model table is missing required fields: {', '.join(missing)}")
        rows: list[dict[str, str]] = []
        for values in reader:
            split = values[positions["split"]]
            if split == "locked_test":
                rows.append(
                    {field: values[positions[field]] for field in safe_locked_fields}
                )
            else:
                rows.append(dict(zip(header, values, strict=True)))
    return rows


def write_issues(path: Path, issues: list[dict[str, object]]) -> None:
    if not issues:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({field for issue in issues for field in issue})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(issues)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/model_team_innings.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/full_cohort_analysis_audit.json",
    )
    parser.add_argument(
        "--issues-output",
        type=Path,
        default=ROOT / "artifacts/tables/full_cohort_analysis_issues.csv",
    )
    args = parser.parse_args()

    rows = read_without_locked_outcomes(args.input)
    summary, issues = audit_unlocked_model_rows(rows)
    summary["input"] = str(args.input)
    summary["issues_output"] = str(args.issues_output)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_issues(args.issues_output, issues)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
