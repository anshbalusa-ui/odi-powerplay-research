from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.audit import (  # noqa: E402
    AUDIT_FIELDS,
    audit_raw_against_processed,
    select_audit_match_ids,
)
from odi_powerplay.extract_cricsheet import extract_match  # noqa: E402


class ExtractionAuditTests(unittest.TestCase):
    def test_select_audit_match_ids_is_deterministic_unique_and_spans_years(self) -> None:
        rows = [
            {"match_id": str(index), "year": 2015 + index % 3}
            for index in range(30)
        ]

        first = select_audit_match_ids(rows, n=9, seed=20250905)
        second = select_audit_match_ids(rows, n=9, seed=20250905)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 9)
        self.assertEqual(len(set(first)), 9)
        selected_years = {
            row["year"] for row in rows if str(row["match_id"]) in set(first)
        }
        self.assertEqual(selected_years, {2015, 2016, 2017})

    def test_audit_detects_a_mutated_processed_powerplay_value(self) -> None:
        fixture = PROJECT_ROOT / "tests" / "fixtures" / "minimal_odi.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            raw_dir = Path(temporary_directory)
            raw_match = raw_dir / "audit-match.json"
            shutil.copyfile(fixture, raw_match)
            processed = extract_match(raw_match)
            processed[0] = dict(processed[0], pp_runs=999)

            audit = audit_raw_against_processed(
                raw_dir,
                processed,
                ["audit-match"],
            )

        discrepancies = [
            row
            for row in audit
            if row["field"] == "pp_runs" and row["matches"] == 0
        ]
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0]["processed_value"], 999)
        self.assertEqual(discrepancies[0]["reextracted_value"], 16)

    def test_audit_covers_every_declared_field_for_both_innings(self) -> None:
        fixture = PROJECT_ROOT / "tests" / "fixtures" / "minimal_odi.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            raw_dir = Path(temporary_directory)
            raw_match = raw_dir / "audit-match.json"
            shutil.copyfile(fixture, raw_match)
            processed = extract_match(raw_match)

            audit = audit_raw_against_processed(
                raw_dir,
                processed,
                ["audit-match"],
            )

        self.assertEqual(len(audit), 2 * len(AUDIT_FIELDS))
        self.assertTrue(all(row["matches"] == 1 for row in audit))


if __name__ == "__main__":
    unittest.main()
