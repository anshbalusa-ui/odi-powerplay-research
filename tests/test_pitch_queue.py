from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.pitch_queue import build_pitch_queue  # noqa: E402


class PitchQueueTests(unittest.TestCase):
    def test_one_outcome_blind_row_is_created_per_match(self) -> None:
        rows = [
            {
                "match_id": "123",
                "match_date": "2023-10-05",
                "year": 2023,
                "venue": "Narendra Modi Stadium",
                "city": "Ahmedabad",
                "event_name": "ICC Cricket World Cup",
                "competition_type": "world_cup",
                "batting_team": "England",
                "opponent": "New Zealand",
                "innings_number": 1,
                "winner": "New Zealand",
                "batting_team_won": 0,
                "pp_runs": 51,
                "pp_wickets": 1,
            },
            {
                "match_id": "123",
                "match_date": "2023-10-05",
                "year": 2023,
                "venue": "Narendra Modi Stadium",
                "city": "Ahmedabad",
                "event_name": "ICC Cricket World Cup",
                "competition_type": "world_cup",
                "batting_team": "New Zealand",
                "opponent": "England",
                "innings_number": 2,
                "winner": "New Zealand",
                "batting_team_won": 1,
                "pp_runs": 81,
                "pp_wickets": 1,
            },
        ]

        queue = build_pitch_queue(rows)

        self.assertEqual(len(queue), 1)
        item = queue[0]
        self.assertEqual(item["cricsheet_match_id"], "123")
        self.assertEqual(item["team_1"], "England")
        self.assertEqual(item["team_2"], "New Zealand")
        self.assertIn("ESPNcricinfo", item["search_query"])
        self.assertIn("2023-10-05", item["search_query"])
        forbidden = {"winner", "batting_team_won", "pp_runs", "pp_wickets"}
        self.assertTrue(forbidden.isdisjoint(item))

    def test_queue_is_stably_sorted_by_date_then_match_id(self) -> None:
        rows = [
            {
                "match_id": "b",
                "match_date": "2024-01-02",
                "year": 2024,
                "venue": "B Ground",
                "city": "B City",
                "event_name": "Series B",
                "competition_type": "bilateral_series",
                "batting_team": "B1",
                "opponent": "B2",
                "innings_number": 1,
            },
            {
                "match_id": "a",
                "match_date": "2024-01-01",
                "year": 2024,
                "venue": "A Ground",
                "city": "A City",
                "event_name": "Series A",
                "competition_type": "bilateral_series",
                "batting_team": "A1",
                "opponent": "A2",
                "innings_number": 1,
            },
        ]
        queue = build_pitch_queue(rows)
        self.assertEqual([item["cricsheet_match_id"] for item in queue], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
