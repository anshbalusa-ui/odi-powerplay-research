#!/usr/bin/env python3
"""Build date-batched pre-match Elo and rolling-win-rate features."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.strength import (  # noqa: E402
    calculate_prematch_strength,
    innings_rows_to_matches,
    write_strength_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/team_strength_pre_match.csv",
    )
    parser.add_argument("--initial-rating", type=float, default=1500.0)
    parser.add_argument("--k-factor", type=float, default=20.0)
    parser.add_argument("--rolling-window", type=int, default=20)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8", newline="") as handle:
        innings_rows = list(csv.DictReader(handle))
    matches = innings_rows_to_matches(innings_rows)
    strength_rows = calculate_prematch_strength(
        matches,
        initial_rating=args.initial_rating,
        k_factor=args.k_factor,
        rolling_window=args.rolling_window,
    )
    write_strength_csv(strength_rows, args.output)

    first_appearance_count = sum(
        int(row["team_1_prior_matches"] == 0) + int(row["team_2_prior_matches"] == 0)
        for row in strength_rows
    )
    summary = {
        "matches": len(strength_rows),
        "unique_match_ids": len({row["match_id"] for row in strength_rows}),
        "first_team_appearances": first_appearance_count,
        "initial_rating": args.initial_rating,
        "k_factor": args.k_factor,
        "rolling_window": args.rolling_window,
        "output": str(args.output.relative_to(PROJECT_ROOT)),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
