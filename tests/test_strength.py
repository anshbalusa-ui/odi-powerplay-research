from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.strength import calculate_prematch_strength, match_rows_from_innings


class TeamStrengthTests(unittest.TestCase):
    def matches(self) -> list[dict[str, str]]:
        return [
            {
                "match_id": "same-day-1",
                "match_date": "2020-01-01",
                "team_1": "A",
                "team_2": "B",
                "winner": "A",
            },
            {
                "match_id": "same-day-2",
                "match_date": "2020-01-01",
                "team_1": "A",
                "team_2": "C",
                "winner": "A",
            },
            {
                "match_id": "next-day",
                "match_date": "2020-01-02",
                "team_1": "A",
                "team_2": "D",
                "winner": "D",
            },
        ]

    def test_same_date_matches_share_the_same_pre_match_state(self) -> None:
        output = calculate_prematch_strength(self.matches())
        first, second, third = output
        self.assertEqual(first["team_1_elo_pre"], 1500.0)
        self.assertEqual(second["team_1_elo_pre"], 1500.0)
        self.assertEqual(first["team_1_prior_matches"], 0)
        self.assertEqual(second["team_1_prior_matches"], 0)
        self.assertIsNone(first["team_1_prior20_win_rate"])
        self.assertEqual(third["team_1_elo_pre"], 1520.0)
        self.assertEqual(third["team_1_prior_matches"], 2)
        self.assertEqual(third["team_1_prior20_win_rate"], 1.0)

    def test_strength_is_independent_of_input_order(self) -> None:
        forward = calculate_prematch_strength(self.matches())
        reverse = calculate_prematch_strength(reversed(self.matches()))
        self.assertEqual(forward, reverse)

    def test_rolling_window_does_not_change_total_prior_match_count(self) -> None:
        matches = [
            {
                "match_id": f"match-{day}",
                "match_date": f"2020-01-{day:02d}",
                "team_1": "A",
                "team_2": f"Opponent {day}",
                "winner": "A" if day > 1 else f"Opponent {day}",
            }
            for day in range(1, 5)
        ]
        output = calculate_prematch_strength(matches, rolling_window=2)
        self.assertEqual(output[-1]["team_1_prior_matches"], 3)
        self.assertEqual(output[-1]["team_1_prior20_win_rate"], 1.0)

    def test_collapses_two_innings_to_one_match_row(self) -> None:
        rows = [
            {
                "match_id": "match-1",
                "match_date": "2020-01-01",
                "innings_number": 1,
                "batting_team": "A",
                "opponent": "B",
                "winner": "B",
            },
            {
                "match_id": "match-1",
                "match_date": "2020-01-01",
                "innings_number": 2,
                "batting_team": "B",
                "opponent": "A",
                "winner": "B",
            },
        ]
        self.assertEqual(
            match_rows_from_innings(rows),
            [
                {
                    "match_id": "match-1",
                    "match_date": "2020-01-01",
                    "team_1": "A",
                    "team_2": "B",
                    "winner": "B",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
