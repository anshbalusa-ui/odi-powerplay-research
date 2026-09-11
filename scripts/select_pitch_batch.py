#!/usr/bin/env python3
"""Select an outcome-blind batch for manual pitch-source coding."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import select_next_pitch_batch  # noqa: E402

FORBIDDEN_COLUMNS = {
    "batting_team_won",
    "winner",
    "pp_runs",
    "pp_wickets",
    "pp_boundary_pct",
    "pp_dot_ball_pct",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data/manual/pitch_collection_queue_template.csv",
    )
    parser.add_argument(
        "--completed",
        type=Path,
        default=ROOT / "data/manual/pitch_reports.csv",
        help="Optional ignored working file; rows marked 0 or 1 are skipped.",
    )
    parser.add_argument(
        "--ignore-completed",
        action="store_true",
        help="Ignore any local working file when regenerating a fixed template.",
    )
    parser.add_argument("--n", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20250905)
    parser.add_argument(
        "--newest-first",
        action="store_true",
        help="Select the newest unreviewed matches instead of balancing year strata.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/pitch_batch_001_template.csv",
    )
    args = parser.parse_args()

    queue = read_csv(args.queue)
    completed_ids: set[str] = set()
    if not args.ignore_completed and args.completed.is_file():
        completed_ids = {
            str(row["cricsheet_match_id"])
            for row in read_csv(args.completed)
            if str(row.get("pre_match_verified", "")).strip() in {"0", "1"}
        }
    batch = select_next_pitch_batch(
        queue,
        completed_match_ids=completed_ids,
        n=args.n,
        seed=args.seed,
        newest_first=args.newest_first,
    )
    if not batch:
        raise ValueError("No uncompleted pitch-source rows remain")
    leaked = sorted(set(batch[0]) & FORBIDDEN_COLUMNS)
    if leaked:
        raise ValueError(f"Outcome-bearing columns entered the batch: {', '.join(leaked)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(batch[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(batch)

    summary = {
        "selected_matches": len(batch),
        "completed_matches_skipped": len(completed_ids),
        "seed": args.seed,
        "selection_strategy": "newest_first" if args.newest_first else "balanced",
        "match_date_range": [batch[-1]["match_date"], batch[0]["match_date"]]
        if args.newest_first
        else [min(row["match_date"] for row in batch), max(row["match_date"] for row in batch)],
        "years": dict(sorted(Counter(row["match_date"][:4] for row in batch).items())),
        "competition_types": dict(
            sorted(Counter(row["competition_type"] for row in batch).items())
        ),
        "output": str(args.output),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
