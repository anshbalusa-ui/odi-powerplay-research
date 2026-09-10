from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.strength import (  # noqa: E402
    calculate_prematch_strength,
    innings_rows_to_matches,
)


def match(
    match_id: str,
    match_date: str,
    team_1: str,
    team_2: str,
    winner: str,
) -> dict[str, str]:
    return {
        "match_id": match_id,
        "match_date": match_date,
        "team_1": team_1,
        "team_2": team_2,
        "winner": winner,
    }


class TeamStrengthTests(unittest.TestCase):
    def test_innings_rows_collapse_to_one_match_in_first_innings_order(self) -> None:
        innings = [
            {
                "match_id": "m1",
                "match_date": "2020-01-01",
                "innings_number": "2",
                "batting_team": "B",
                "opponent": "A",
                "winner": "A",
            },
            {
                "match_id": "m1",
                "match_date": "2020-01-01",
                "innings_number": "1",
                "batting_team": "A",
                "opponent": "B",
                "winner": "A",
            },
        ]

        self.assertEqual(
            innings_rows_to_matches(innings),
            [
                {
                    "match_id": "m1",
                    "match_date": "2020-01-01",
                    "team_1": "A",
                    "team_2": "B",
                    "winner": "A",
                }
            ],
        )

    def test_same_day_matches_use_ratings_before_any_same_day_update(self) -> None:
        rows = [
            match("a", "2020-01-01", "A", "B", "A"),
            match("b", "2020-01-01", "A", "C", "C"),
        ]

        output = calculate_prematch_strength(rows)

        self.assertEqual(output[0]["team_1_elo_pre"], 1500.0)
        self.assertEqual(output[1]["team_1_elo_pre"], 1500.0)

    def test_later_date_receives_prior_date_elo_updates(self) -> None:
        rows = [
            match("a", "2020-01-01", "A", "B", "A"),
            match("b", "2020-01-02", "A", "B", "B"),
        ]

        output = calculate_prematch_strength(rows, k_factor=20.0)

        self.assertEqual(output[1]["team_1_elo_pre"], 1510.0)
        self.assertEqual(output[1]["team_2_elo_pre"], 1490.0)
        self.assertEqual(output[1]["elo_difference_team_1"], 20.0)

    def test_same_day_matches_do_not_enter_prior_win_rate_history(self) -> None:
        rows = [
            match("a", "2020-01-01", "A", "B", "A"),
            match("b", "2020-01-01", "A", "C", "C"),
            match("c", "2020-01-02", "A", "D", "A"),
        ]

        output = calculate_prematch_strength(rows, rolling_window=20)

        self.assertEqual(output[0]["team_1_prior_matches"], 0)
        self.assertEqual(output[1]["team_1_prior_matches"], 0)
        self.assertEqual(output[2]["team_1_prior_matches"], 2)
        self.assertEqual(output[2]["team_1_rolling_win_rate"], 0.5)

    def test_duplicate_match_ids_are_rejected(self) -> None:
        rows = [
            match("duplicate", "2020-01-01", "A", "B", "A"),
            match("duplicate", "2020-01-02", "C", "D", "D"),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate match_id"):
            calculate_prematch_strength(rows)


if __name__ == "__main__":
    unittest.main()
