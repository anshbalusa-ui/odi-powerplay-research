#!/usr/bin/env python3
"""Build leakage-safe pre-match Elo and rolling win-rate features."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.strength import (  # noqa: E402
    calculate_prematch_strength,
    match_rows_from_innings,
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
        default=ROOT / "data/processed/team_strength_pre_match.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "artifacts/tables/team_strength_audit.json",
    )
    parser.add_argument("--initial-rating", type=float, default=1500.0)
    parser.add_argument("--k-factor", type=float, default=20.0)
    parser.add_argument("--rolling-window", type=int, default=20)
    args = parser.parse_args()

    history_rows = read_csv(args.history_input)
    primary_ids = {row["match_id"] for row in read_csv(args.primary_input)}
    matches = match_rows_from_innings(history_rows)
    all_strength = calculate_prematch_strength(
        matches,
        initial_rating=args.initial_rating,
        k_factor=args.k_factor,
        rolling_window=args.rolling_window,
    )
    output_rows = [row for row in all_strength if row["match_id"] in primary_ids]
    if {row["match_id"] for row in output_rows} != primary_ids:
        raise ValueError("Strength output does not cover every primary match exactly once")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "history_matches": len(matches),
        "primary_matches": len(primary_ids),
        "output_matches": len(output_rows),
        "initial_rating": args.initial_rating,
        "k_factor": args.k_factor,
        "rolling_window": args.rolling_window,
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "cold_start_team_1_rows": sum(row["team_1_prior_matches"] == 0 for row in output_rows),
        "cold_start_team_2_rows": sum(row["team_2_prior_matches"] == 0 for row in output_rows),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
