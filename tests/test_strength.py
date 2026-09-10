from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.strength import add_pre_match_elo  # noqa: E402


def innings(match_id: str, date: str, batting_team: str, opponent: str, winner: str, innings_number: int):
    return {
        "match_id": match_id,
        "match_date": date,
        "batting_team": batting_team,
        "opponent": opponent,
        "winner": winner,
        "innings_number": innings_number,
    }


class EloTests(unittest.TestCase):
    def test_later_date_uses_only_prior_match_result(self) -> None:
        rows = [
            innings("m1", "2024-01-01", "Alpha", "Beta", "Alpha", 1),
            innings("m1", "2024-01-01", "Beta", "Alpha", "Alpha", 2),
            innings("m2", "2024-01-02", "Alpha", "Gamma", "Gamma", 1),
            innings("m2", "2024-01-02", "Gamma", "Alpha", "Gamma", 2),
        ]
        enriched = add_pre_match_elo(rows, initial_rating=1500.0, k_factor=20.0)
        by_key = {(row["match_id"], row["batting_team"]): row for row in enriched}

        self.assertEqual(by_key[("m1", "Alpha")]["team_elo_pre"], 1500.0)
        self.assertEqual(by_key[("m1", "Beta")]["team_elo_pre"], 1500.0)
        self.assertAlmostEqual(by_key[("m2", "Alpha")]["team_elo_pre"], 1510.0, places=6)
        self.assertEqual(by_key[("m2", "Gamma")]["team_elo_pre"], 1500.0)
        self.assertAlmostEqual(by_key[("m2", "Alpha")]["elo_difference"], 10.0, places=6)

    def test_same_date_matches_are_batched_without_intra_day_leakage(self) -> None:
        rows = [
            innings("m1", "2024-01-01", "Alpha", "Beta", "Alpha", 1),
            innings("m1", "2024-01-01", "Beta", "Alpha", "Alpha", 2),
            innings("m2", "2024-01-01", "Alpha", "Gamma", "Gamma", 1),
            innings("m2", "2024-01-01", "Gamma", "Alpha", "Gamma", 2),
        ]
        enriched = add_pre_match_elo(rows, initial_rating=1500.0, k_factor=20.0)
        alpha_rows = [row for row in enriched if row["batting_team"] == "Alpha"]

        self.assertEqual(len(alpha_rows), 2)
        self.assertTrue(all(row["team_elo_pre"] == 1500.0 for row in alpha_rows))
        self.assertTrue(all(row["opponent_elo_pre"] == 1500.0 for row in alpha_rows))

    def test_excluded_prior_match_can_still_inform_strength_history(self) -> None:
        prior = [
            innings("rain_game", "2024-01-01", "Alpha", "Beta", "Alpha", 1),
            innings("rain_game", "2024-01-01", "Beta", "Alpha", "Alpha", 2),
        ]
        target = [
            innings("clean_game", "2024-01-02", "Alpha", "Gamma", "Gamma", 1),
            innings("clean_game", "2024-01-02", "Gamma", "Alpha", "Gamma", 2),
        ]
        enriched = add_pre_match_elo(
            target,
            history_rows=[*prior, *target],
            initial_rating=1500.0,
            k_factor=20.0,
        )
        alpha = next(row for row in enriched if row["batting_team"] == "Alpha")
        self.assertAlmostEqual(alpha["team_elo_pre"], 1510.0, places=6)
        self.assertAlmostEqual(alpha["elo_difference"], 10.0, places=6)


if __name__ == "__main__":
    unittest.main()
