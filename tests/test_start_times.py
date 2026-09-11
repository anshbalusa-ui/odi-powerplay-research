from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.start_times import (
    START_TIME_FIELDS,
    build_match_start_queue,
    match_start_coverage_summary,
    validate_match_start_rows,
    verified_match_start_map,
)


class MatchStartTimeTests(unittest.TestCase):
    def innings_rows(self) -> list[dict[str, object]]:
        shared = {
            "match_id": "1000887",
            "match_date": "2026-01-02",
            "event_name": "Fixture ODI Series",
            "competition_type": "bilateral_series",
            "venue": "Fixture Ground",
            "city": "Fixture City",
            "winner": "Team A",
            "pp_runs": 55,
        }
        return [
            {
                **shared,
                "innings_number": 1,
                "batting_team": "Team A",
                "opponent": "Team B",
            },
            {
                **shared,
                "innings_number": 2,
                "batting_team": "Team B",
                "opponent": "Team A",
            },
        ]

    def verified_row(self) -> dict[str, object]:
        row = build_match_start_queue(self.innings_rows())[0]
        return {
            **row,
            "source_url": "https://example.org/official-schedule",
            "source_title": "Official match schedule",
            "accessed_at_utc": "2026-01-01T12:00:00Z",
            "scheduled_start_local": "2026-01-02T09:00:00",
            "timezone_name": "Asia/Kolkata",
            "scheduled_start_utc": "2026-01-02T03:30:00Z",
            "start_time_status": "verified",
            "verifier_id": "coder-1",
        }

    def test_queue_is_outcome_blind_and_has_stable_schema(self) -> None:
        class GuardedRow(dict):
            def __getitem__(self, key):
                if key in {"winner", "pp_runs", "batting_team_won"}:
                    raise AssertionError(f"Outcome-bearing field was read: {key}")
                return super().__getitem__(key)

            def get(self, key, default=None):
                if key in {"winner", "pp_runs", "batting_team_won"}:
                    raise AssertionError(f"Outcome-bearing field was read: {key}")
                return super().get(key, default)

        queue = build_match_start_queue(GuardedRow(row) for row in self.innings_rows())
        self.assertEqual(len(queue), 1)
        self.assertEqual(tuple(queue[0]), START_TIME_FIELDS)
        self.assertEqual(queue[0]["start_time_status"], "pending")
        self.assertNotIn("winner", queue[0])
        self.assertNotIn("pp_runs", queue[0])
        self.assertIn("scheduled start time", queue[0]["source_search_query"])

    def test_verified_local_time_must_match_iana_timezone_and_utc(self) -> None:
        reference = build_match_start_queue(self.innings_rows())
        row = self.verified_row()
        self.assertEqual(validate_match_start_rows([row], eligible_rows=reference), [])

        mismatched = {**row, "scheduled_start_utc": "2026-01-02T04:30:00Z"}
        self.assertEqual(
            {issue["message"] for issue in validate_match_start_rows([mismatched])},
            {"does not equal the local start converted with timezone_name"},
        )

        unknown_zone = {**row, "timezone_name": "Fixture/Nowhere"}
        self.assertIn(
            "unknown IANA timezone",
            {issue["message"] for issue in validate_match_start_rows([unknown_zone])},
        )

    def test_verified_row_requires_provenance_and_cohort_identity(self) -> None:
        reference = build_match_start_queue(self.innings_rows())
        row = self.verified_row()
        invalid = {
            **row,
            "venue": "Wrong Ground",
            "source_url": "not-a-url",
            "source_title": "",
            "accessed_at_utc": "2026-01-01",
            "verifier_id": "",
        }
        fields = {
            issue["field"]
            for issue in validate_match_start_rows([invalid], eligible_rows=reference)
        }
        self.assertTrue(
            {"venue", "source_url", "source_title", "accessed_at_utc", "verifier_id"} <= fields
        )

    def test_reference_requires_one_row_for_every_eligible_match(self) -> None:
        reference = build_match_start_queue(self.innings_rows())
        issues = validate_match_start_rows([], eligible_rows=reference)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["message"], "eligible match is missing from start-time file")

    def test_only_verified_rows_enter_timestamp_map(self) -> None:
        pending = build_match_start_queue(self.innings_rows())[0]
        verified = self.verified_row()
        self.assertEqual(verified_match_start_map([pending]), {})
        self.assertEqual(
            verified_match_start_map([verified]),
            {"1000887": "2026-01-02T03:30:00Z"},
        )
        summary = match_start_coverage_summary([verified])
        self.assertEqual(summary["verified_start_times"], 1)
        self.assertEqual(summary["coverage_pct"], 100.0)

    def test_unavailable_status_requires_exclusion_reason(self) -> None:
        row = build_match_start_queue(self.innings_rows())[0]
        unavailable = {**row, "start_time_status": "unavailable"}
        self.assertEqual(
            {issue["field"] for issue in validate_match_start_rows([unavailable])},
            {"exclusion_reason"},
        )


if __name__ == "__main__":
    unittest.main()
