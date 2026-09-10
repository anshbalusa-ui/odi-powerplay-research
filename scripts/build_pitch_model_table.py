#!/usr/bin/env python3
"""Merge validated pre-match pitch codes into the team-innings model table."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import merge_pitch_conditions, validate_pitch_rows  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitch-input", type=Path, required=True)
    parser.add_argument("--match-start-input", type=Path, required=True)
    parser.add_argument(
        "--innings-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/processed/powerplay_pitch_model_table.csv",
    )
    args = parser.parse_args()

    innings_rows = read_csv(args.innings_input)
    pitch_rows = read_csv(args.pitch_input)
    match_starts = {
        row["cricsheet_match_id"]: row.get("scheduled_start_utc", "")
        for row in read_csv(args.match_start_input)
    }
    issues = validate_pitch_rows(
        pitch_rows,
        eligible_match_ids={row["match_id"] for row in innings_rows},
        match_start_by_id=match_starts,
    )
    if issues:
        fields = sorted({issue["field"] for issue in issues})
        raise ValueError(
            f"Pitch data has {len(issues)} validation issues in fields: {', '.join(fields)}"
        )

    merged = merge_pitch_conditions(innings_rows, pitch_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(merged[0]))
        writer.writeheader()
        writer.writerows(merged)
    covered = sum(int(row["pitch_available"]) for row in merged) // 2
    print(f"Wrote {len(merged)} innings rows with verified pitch codes for {covered} matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
