#!/usr/bin/env python3
"""Build or apply a raw-preserving pitch reliability reconciliation worksheet."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (  # noqa: E402
    PITCH_FIELDS,
    RECONCILIATION_FIELDS,
    apply_pitch_reconciliation,
    build_pitch_reliability_disagreements,
    validate_pitch_rows,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def worksheet_fieldnames(rows: list[dict[str, str]]) -> list[str]:
    if rows:
        return list(rows[0])
    fields = [
        "cricsheet_match_id",
        "sample_sequence",
        "match_date",
        "source_url",
        "source_title",
    ]
    for field in (*RECONCILIATION_FIELDS, "short_paraphrased_note"):
        fields.extend(
            (
                f"coder1_{field}",
                f"coder2_{field}",
                f"disagreement_{field}",
                f"reconciled_{field}",
            )
        )
    fields.extend(
        (
            "disagreement_fields",
            "disagreement_count",
            "reconciliation_status",
            "reconciled_changed_from_coder1",
            "reconciled_by",
            "reconciled_at_utc",
            "reconciliation_note",
        )
    )
    return fields


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-input", type=Path, required=True)
    parser.add_argument("--recoded-input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_reconciliation_worksheet.csv",
    )
    parser.add_argument(
        "--reconciliation-input",
        type=Path,
        help="Completed worksheet to apply instead of building a new worksheet.",
    )
    parser.add_argument(
        "--final-output",
        type=Path,
        help="Separate reconciled release written when --reconciliation-input is used.",
    )
    args = parser.parse_args()

    reference_rows = read_csv(args.reference_input)
    recoded_rows = read_csv(args.recoded_input)
    for coding_set, rows in (("reference", reference_rows), ("recoded", recoded_rows)):
        issues = validate_pitch_rows(rows)
        if issues:
            print(
                json.dumps(
                    {
                        "mode": "validation_failed",
                        "coding_set": coding_set,
                        "issue_count": len(issues),
                        "issues": issues,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1

    if args.reconciliation_input is None:
        worksheet = build_pitch_reliability_disagreements(reference_rows, recoded_rows)
        write_csv(args.output, worksheet, worksheet_fieldnames(worksheet))
        pending = sum(row["reconciliation_status"] == "pending" for row in worksheet)
        print(
            json.dumps(
                {
                    "mode": "build",
                    "worksheet_output": str(args.output),
                    "paired_rows": len(worksheet),
                    "pending_rows": pending,
                    "raw_inputs_modified": False,
                    "final_values_separate_from_raw": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.final_output is None:
        parser.error("--final-output is required with --reconciliation-input")
    reconciliation_rows = read_csv(args.reconciliation_input)
    final_rows = apply_pitch_reconciliation(reference_rows, reconciliation_rows)
    final_fields = list(reference_rows[0]) if reference_rows else list(PITCH_FIELDS)
    for field in (
        "reconciliation_status",
        "reconciliation_changed_from_coder1",
        "reconciled_by",
        "reconciled_at_utc",
        "reconciliation_note",
        "reconciliation_release",
    ):
        if field not in final_fields:
            final_fields.append(field)
    write_csv(args.final_output, final_rows, final_fields)
    changed = sum(
        str(row.get("reconciliation_changed_from_coder1", "")) == "1"
        for row in final_rows
    )
    print(
        json.dumps(
            {
                "mode": "apply",
                "final_output": str(args.final_output),
                "reference_rows": len(reference_rows),
                "changed_rows": changed,
                "raw_inputs_modified": False,
                "second_coder_answers_overwritten": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
