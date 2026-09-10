#!/usr/bin/env python3
"""Select the next outcome-blind pitch-report collection batch."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.pitch import select_next_pitch_batch  # noqa: E402


DEFAULT_QUOTAS = {
    "bilateral_series": 3,
    "qualification_pathway": 3,
    "multi_team_series": 2,
    "world_cup": 1,
    "champions_trophy": 1,
    "continental_cup": 1,
    "other_odi": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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
        default=PROJECT_ROOT / "data/manual/pitch_reports.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/manual/pitch_batch_002.csv",
    )
    parser.add_argument("--seed", type=int, default=20250905)
    args = parser.parse_args()

    primary_rows = [
        row for row in read_csv(args.matches) if int(row["innings_number"]) == 1
    ]
    pitch_rows = read_csv(args.pitch_registry) if args.pitch_registry.exists() else []
    audited_ids = {row["cricsheet_match_id"] for row in pitch_rows}
    selected = select_next_pitch_batch(
        primary_rows,
        audited_ids=audited_ids,
        quotas=DEFAULT_QUOTAS,
        seed=args.seed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)

    print(
        json.dumps(
            {
                "selected_matches": len(selected),
                "already_audited_matches": len(audited_ids),
                "competition_counts": {
                    competition: sum(
                        row["competition_type"] == competition for row in selected
                    )
                    for competition in DEFAULT_QUOTAS
                },
                "output": str(args.output.relative_to(PROJECT_ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
