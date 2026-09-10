from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.pitch import (  # noqa: E402
    select_next_pitch_batch,
    validate_pitch_rows,
)


def valid_pitch_row(**updates: str) -> dict[str, str]:
    row = {
        "cricsheet_match_id": "m1",
        "match_date": "2024-01-02",
        "venue": "Example Ground",
        "source_url": "https://example.org/preview",
        "source_title": "Match preview",
        "published_at_utc": "2024-01-02T08:00:00Z",
        "accessed_at_utc": "2026-09-09T12:00:00Z",
        "pre_match_verified": "1",
        "coder_id": "coder_a",
        "coder_confidence": "high",
        "pitch_primary_category": "pace_seam",
        "batting_ease": "1",
        "pace_seam_support": "2",
        "spin_support": "0",
        "bounce_profile": "standard",
        "two_paced_expected": "0",
        "dew_expected": "",
        "short_paraphrased_note": "Expected early seam movement and true bounce.",
        "exclusion_reason": "",
    }
    row.update(updates)
    return row


def match_index() -> dict[str, dict[str, str]]:
    return {
        "m1": {
            "match_id": "m1",
            "match_date": "2024-01-02",
            "venue": "Example Ground",
            "match_start_utc": "2024-01-02T10:00:00Z",
        }
    }


class PitchValidationTests(unittest.TestCase):
    def test_post_match_source_is_rejected(self) -> None:
        row = valid_pitch_row(published_at_utc="2024-01-02T12:00:00Z")

        usable, issues = validate_pitch_rows([row], match_index())

        self.assertEqual(usable, [])
        self.assertTrue(
            any(issue["issue_code"] == "SOURCE_NOT_PRE_MATCH" for issue in issues)
        )

    def test_documented_pitch_scales_reject_out_of_range_values(self) -> None:
        row = valid_pitch_row(batting_ease="4")

        usable, issues = validate_pitch_rows([row], match_index())

        self.assertEqual(usable, [])
        self.assertTrue(
            any(issue["issue_code"] == "INVALID_BATTING_EASE" for issue in issues)
        )

    def test_explicit_zero_is_preserved_as_a_valid_code(self) -> None:
        row = valid_pitch_row(
            batting_ease="0",
            pace_seam_support="0",
            spin_support="0",
            two_paced_expected="0",
        )

        usable, issues = validate_pitch_rows([row], match_index())

        self.assertEqual(len(usable), 1)
        self.assertFalse(any(issue["severity"] == "error" for issue in issues))
        self.assertEqual(usable[0]["batting_ease"], 0)
        self.assertEqual(usable[0]["two_paced_expected"], 0)

    def test_outcome_and_powerplay_values_cannot_change_batch_selection(self) -> None:
        base_matches = [
            {
                "match_id": f"m{index}",
                "match_date": f"202{index}-01-01",
                "venue": f"Ground {index}",
                "competition_type": "bilateral_series",
            }
            for index in range(5)
        ]
        altered = [
            dict(row, batting_team_won=index % 2, pp_runs=999 - index)
            for index, row in enumerate(base_matches)
        ]

        first = select_next_pitch_batch(
            base_matches,
            audited_ids=set(),
            quotas={"bilateral_series": 2},
            seed=20250905,
        )
        second = select_next_pitch_batch(
            altered,
            audited_ids=set(),
            quotas={"bilateral_series": 2},
            seed=20250905,
        )

        self.assertEqual(first, second)
        self.assertTrue(all("batting_team_won" not in row for row in first))
        self.assertTrue(all("pp_runs" not in row for row in first))


if __name__ == "__main__":
    unittest.main()
