#!/usr/bin/env python3
"""Build leakage-safe rolling pre-match venue-condition features."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.venue import (  # noqa: E402
    calculate_prematch_venue_conditions,
    venue_match_rows_from_innings,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_clean.csv",
    )
    parser.add_argument(
        "--primary-input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/processed/venue_conditions_pre_match.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/venue_conditions_audit.json",
    )
    parser.add_argument("--rolling-window", type=int, default=20)
    args = parser.parse_args()

    history_rows = read_csv(args.history_input)
    primary_ids = {row["match_id"] for row in read_csv(args.primary_input)}
    matches = venue_match_rows_from_innings(history_rows)
    all_conditions = calculate_prematch_venue_conditions(
        matches,
        rolling_window=args.rolling_window,
    )
    output_rows = [row for row in all_conditions if row["match_id"] in primary_ids]
    if len(output_rows) != len(primary_ids):
        raise ValueError("Venue-condition output must contain every primary match exactly once")
    if {str(row["match_id"]) for row in output_rows} != primary_ids:
        raise ValueError("Venue-condition output match IDs differ from the primary cohort")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    rows_with_history = sum(bool(row["venue_history_available"]) for row in output_rows)
    summary = {
        "history_matches": len(matches),
        "primary_matches": len(primary_ids),
        "output_matches": len(output_rows),
        "rolling_window": args.rolling_window,
        "matches_with_prior_venue_history": rows_with_history,
        "cold_start_matches": len(output_rows) - rows_with_history,
        "coverage_pct": round(100 * rows_with_history / len(output_rows), 6),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
