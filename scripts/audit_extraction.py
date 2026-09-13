#!/usr/bin/env python3
"""Re-extract a deterministic match sample and compare it with saved rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.audit import (  # noqa: E402
    AUDIT_FIELDS,
    audit_raw_against_processed,
    select_audit_match_ids,
    write_audit_csv,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data/raw/cricsheet",
    )
    parser.add_argument(
        "--selection-table",
        type=Path,
        default=PROJECT_ROOT / "data/processed/powerplay_innings_primary.csv",
    )
    parser.add_argument(
        "--processed-table",
        type=Path,
        default=PROJECT_ROOT / "data/interim/powerplay_innings_all.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "artifacts/tables/extraction_audit.csv",
    )
    parser.add_argument("--n-matches", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20250905)
    args = parser.parse_args()

    selection_rows = read_csv(args.selection_table)
    selected_ids = select_audit_match_ids(
        selection_rows,
        n=args.n_matches,
        seed=args.seed,
    )
    selected_set = set(selected_ids)
    processed_rows = [
        row for row in read_csv(args.processed_table) if row["match_id"] in selected_set
    ]
    audit_rows = audit_raw_against_processed(
        args.raw_dir,
        processed_rows,
        selected_ids,
    )
    write_audit_csv(audit_rows, args.output)

    discrepancy_rows = [row for row in audit_rows if row["matches"] != 1]
    audited_innings = len(audit_rows) // len(AUDIT_FIELDS)
    summary = {
        "selected_matches": len(selected_ids),
        "audited_innings": audited_innings,
        "field_comparisons": len(audit_rows),
        "discrepancies": len(discrepancy_rows),
        "selected_match_ids": selected_ids,
        "output": str(args.output.relative_to(PROJECT_ROOT)),
    }
    print(json.dumps(summary, indent=2))
    if discrepancy_rows:
        raise SystemExit("Extraction audit found one or more discrepancies")


if __name__ == "__main__":
    main()
