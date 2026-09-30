#!/usr/bin/env python3
"""Report pitch-code coverage and sparse interaction cells without using outcomes."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import PITCH_FIELDS  # noqa: E402


def read_pitch_rows(path: Path) -> list[dict[str, str]]:
    safe_fields = {"match_id", "match_date", "split", *PITCH_FIELDS}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        positions = {field: index for index, field in enumerate(header)}
        missing = sorted(safe_fields - positions.keys())
        if missing:
            raise ValueError(f"Pitch model table is missing fields: {', '.join(missing)}")
        return [
            {field: values[positions[field]] for field in safe_fields}
            for values in reader
        ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/model_team_innings_pitch.csv",
    )
    parser.add_argument(
        "--sparse-match-threshold",
        type=int,
        default=10,
        help="Reporting threshold only; it does not collapse or tune any model category.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_sparsity_diagnostics.json",
    )
    parser.add_argument(
        "--cells-output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_sparsity_cells.csv",
    )
    args = parser.parse_args()
    if args.sparse_match_threshold < 1:
        raise ValueError("--sparse-match-threshold must be positive")

    rows = read_pitch_rows(args.input)
    matches: dict[tuple[str, str], dict[str, str]] = {}
    consistency_issues: list[dict[str, str]] = []
    for row in rows:
        key = (row["split"], row["match_id"])
        previous = matches.get(key)
        if previous is None:
            matches[key] = row
            continue
        for field in PITCH_FIELDS:
            if row[field].strip() != previous[field].strip():
                consistency_issues.append(
                    {
                        "split": row["split"],
                        "match_id": row["match_id"],
                        "field": field,
                        "message": "pitch code differs between paired innings rows",
                    }
                )

    splits = sorted({split for split, _ in matches})
    value_counts: dict[str, dict[str, dict[str, int]]] = {}
    for split in splits:
        split_matches = [row for (row_split, _), row in matches.items() if row_split == split]
        value_counts[split] = {}
        for field in PITCH_FIELDS:
            counts = Counter(row[field].strip() or "unstated" for row in split_matches)
            value_counts[split][field] = dict(sorted(counts.items()))

    dimensions = [
        ("primary_by_batting_ease", "pitch_primary_category", "batting_ease"),
        ("primary_by_pace_seam_support", "pitch_primary_category", "pace_seam_support"),
        ("primary_by_spin_support", "pitch_primary_category", "spin_support"),
        ("primary_by_bounce_profile", "pitch_primary_category", "bounce_profile"),
        ("primary_by_two_paced_expected", "pitch_primary_category", "two_paced_expected"),
        ("primary_by_dew_expected", "pitch_primary_category", "dew_expected"),
    ]
    cell_rows: list[dict[str, object]] = []
    for dimension, first_field, second_field in dimensions:
        for split in splits:
            split_matches = [row for (row_split, _), row in matches.items() if row_split == split]
            cells: Counter[tuple[str, str]] = Counter(
                (
                    row[first_field].strip() or "unstated",
                    row[second_field].strip() or "unstated",
                )
                for row in split_matches
            )
            for (first_value, second_value), match_count in sorted(cells.items()):
                cell_rows.append(
                    {
                        "dimension": dimension,
                        "split": split,
                        "first_field": first_field,
                        "first_value": first_value,
                        "second_field": second_field,
                        "second_value": second_value,
                        "match_count": match_count,
                        "row_count": match_count * 2,
                        "sparse": int(match_count < args.sparse_match_threshold),
                        "threshold_is_reporting_only": 1,
                    }
                )

    args.cells_output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(cell_rows[0]) if cell_rows else ["dimension", "split", "match_count"]
    with args.cells_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(cell_rows)
    summary = {
        "locked_test_outcomes_loaded": False,
        "locked_test_scored": False,
        "rows_read_for_pitch_codes_only": len(rows),
        "matches_by_split": dict(
            sorted(
                Counter(split for split, _ in matches).items()
            )
        ),
        "rows_by_split": dict(sorted(Counter(row["split"] for row in rows).items())),
        "value_counts_by_split": value_counts,
        "interaction_dimensions": [dimension for dimension, _, _ in dimensions],
        "sparse_match_threshold": args.sparse_match_threshold,
        "sparse_cell_count": sum(int(row["sparse"]) for row in cell_rows),
        "consistency_issue_count": len(consistency_issues),
        "cells_output": str(args.cells_output),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(bool(consistency_issues))


if __name__ == "__main__":
    raise SystemExit(main())
