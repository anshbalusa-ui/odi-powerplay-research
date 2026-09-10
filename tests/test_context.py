from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.context import merge_context  # noqa: E402


class ContextMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.innings = [
            {"match_id": "m1", "batting_team": "Alpha", "innings_number": 1, "pp_runs": 52},
            {"match_id": "m1", "batting_team": "Beta", "innings_number": 2, "pp_runs": 47},
        ]

    def test_verified_pitch_and_weather_join_to_both_innings(self) -> None:
        pitch = [
            {
                "cricsheet_match_id": "m1",
                "pre_match_verified": "1",
                "source_url": "https://example.test/preview",
                "pitch_primary_category": "pace_friendly",
                "batting_ease": "low",
                "pace_seam_support": "high",
                "spin_support": "low",
            }
        ]
        weather = [
            {
                "match_id": "m1",
                "weather_status": "ok",
                "temperature_2m_mean_c": "19.4",
                "relative_humidity_2m_mean_pct": "72.0",
            }
        ]

        merged = merge_context(self.innings, pitch_rows=pitch, weather_rows=weather)

        self.assertEqual(len(merged), 2)
        self.assertTrue(all(row["pitch_available"] == 1 for row in merged))
        self.assertTrue(all(row["weather_available"] == 1 for row in merged))
        self.assertTrue(all(row["pitch_primary_category"] == "pace_friendly" for row in merged))
        self.assertTrue(all(row["temperature_2m_mean_c"] == "19.4" for row in merged))

    def test_unverified_pitch_is_not_exposed_as_model_context(self) -> None:
        pitch = [
            {
                "cricsheet_match_id": "m1",
                "pre_match_verified": "0",
                "pitch_primary_category": "batting_friendly",
            }
        ]
        merged = merge_context(self.innings, pitch_rows=pitch, weather_rows=[])
        self.assertTrue(all(row["pitch_available"] == 0 for row in merged))
        self.assertTrue(all("pitch_primary_category" not in row for row in merged))

    def test_duplicate_match_context_rows_raise_instead_of_multiplying_innings(self) -> None:
        weather = [
            {"match_id": "m1", "weather_status": "ok"},
            {"match_id": "m1", "weather_status": "ok"},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate weather row"):
            merge_context(self.innings, pitch_rows=[], weather_rows=weather)


if __name__ == "__main__":
    unittest.main()
