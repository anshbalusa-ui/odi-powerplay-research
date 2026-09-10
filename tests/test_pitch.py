from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.pitch import (
    build_pitch_collection_queue,
    merge_pitch_conditions,
    pitch_coverage_summary,
    validate_pitch_rows,
)


class PitchPipelineTests(unittest.TestCase):
    def innings_rows(self) -> list[dict[str, object]]:
        shared = {
            "match_id": "match-1",
            "match_date": "2026-01-02",
            "year": 2026,
            "event_name": "Fixture ODI Series",
            "competition_type": "bilateral_series",
            "venue": "Fixture Ground",
            "city": "Fixture City",
            "pp_runs": 50,
            "winner": "Team A",
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

    def verified_pitch_row(self) -> dict[str, str]:
        return {
            "cricsheet_match_id": "match-1",
            "match_date": "2026-01-02",
            "source_url": "https://example.com/pre-match-report",
            "source_title": "Pre-match conditions",
            "published_at_utc": "2026-01-01T10:00:00+00:00",
            "accessed_at_utc": "2026-01-01T12:00:00+00:00",
            "pre_match_verified": "1",
            "coder_id": "coder-1",
            "coder_confidence": "high",
            "pitch_primary_category": "pace_seam",
            "batting_ease": "1",
            "pace_seam_support": "2",
            "spin_support": "0",
            "bounce_profile": "steep",
            "two_paced_expected": "0",
            "dew_expected": "",
            "short_paraphrased_note": "Expected grass, carry, and early seam movement.",
            "exclusion_reason": "",
        }

    def test_collection_queue_excludes_outcomes_and_powerplay_metrics(self) -> None:
        queue = build_pitch_collection_queue(self.innings_rows())
        self.assertEqual(len(queue), 1)
        self.assertNotIn("pp_runs", queue[0])
        self.assertNotIn("winner", queue[0])
        self.assertIn("preview pitch conditions", queue[0]["source_search_query"])

    def test_verified_source_must_precede_match_start(self) -> None:
        row = self.verified_pitch_row()
        valid = validate_pitch_rows(
            [row],
            eligible_match_ids={"match-1"},
            match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
        )
        self.assertEqual(valid, [])

        row["published_at_utc"] = "2026-01-02T11:00:00+00:00"
        issues = validate_pitch_rows(
            [row],
            eligible_match_ids={"match-1"},
            match_start_by_id={"match-1": "2026-01-02T10:00:00+00:00"},
        )
        self.assertIn("source was not published before match start", {issue["message"] for issue in issues})

    def test_only_verified_pitch_codes_enter_the_model_table(self) -> None:
        verified = self.verified_pitch_row()
        merged = merge_pitch_conditions(self.innings_rows(), [verified])
        self.assertEqual({row["pitch_available"] for row in merged}, {1})
        self.assertEqual({row["pitch_primary_category"] for row in merged}, {"pace_seam"})
        self.assertNotIn("short_paraphrased_note", merged[0])

        verified["pre_match_verified"] = "0"
        missing = merge_pitch_conditions(self.innings_rows(), [verified])
        self.assertEqual({row["pitch_available"] for row in missing}, {0})

    def test_coverage_summary_uses_only_verified_rows(self) -> None:
        verified = self.verified_pitch_row()
        excluded = {**verified, "cricsheet_match_id": "match-2", "pre_match_verified": "0"}
        summary = pitch_coverage_summary([verified, excluded])
        self.assertEqual(summary["verified_pitch_matches"], 1)
        self.assertEqual(summary["coverage_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
