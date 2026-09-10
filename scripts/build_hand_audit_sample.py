#!/usr/bin/env python3
"""Create the deterministic Gate 2 hand-audit worksheet."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.audit import build_hand_audit_template, select_hand_audit_rows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manual/powerplay_hand_audit_template.csv",
    )
    parser.add_argument("--minimum-innings", type=int, default=20)
    parser.add_argument("--seed", default="odi-powerplay-gate-2-v1")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    sampled = select_hand_audit_rows(
        rows,
        minimum_innings=args.minimum_innings,
        seed=args.seed,
    )
    template = build_hand_audit_template(sampled)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(template[0]))
        writer.writeheader()
        writer.writerows(template)

    match_count = len({row["match_id"] for row in template})
    year_count = len({row["year"] for row in template})
    print(f"Wrote {len(template)} innings from {match_count} matches across {year_count} years")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
