from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.extract_cricsheet import extract_match  # noqa: E402


class ExtractCricsheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = extract_match(PROJECT_ROOT / "tests" / "fixtures" / "minimal_odi.json")

    def test_returns_one_row_per_regulation_innings(self) -> None:
        self.assertEqual(len(self.rows), 2)
        self.assertEqual([row["innings_number"] for row in self.rows], [1, 2])

    def test_first_innings_metrics_use_legal_ball_denominators(self) -> None:
        row = self.rows[0]
        self.assertEqual(row["pp_runs"], 16)
        self.assertEqual(row["pp_wickets"], 1)
        self.assertEqual(row["pp_legal_balls"], 6)
        self.assertEqual(row["pp_delivery_events"], 7)
        self.assertEqual(row["pp_boundary_balls"], 2)
        self.assertAlmostEqual(row["pp_boundary_pct"], 100 * 2 / 6, places=6)
        self.assertEqual(row["pp_dot_balls"], 2)
        self.assertAlmostEqual(row["pp_dot_ball_pct"], 100 * 2 / 6, places=6)
        self.assertEqual(row["pp_run_rate"], 16.0)

    def test_non_boundary_four_is_not_boundary_and_wide_is_not_legal(self) -> None:
        row = self.rows[0]
        self.assertEqual(row["pp_boundary_balls"], 2)
        self.assertEqual(row["pp_legal_balls"], 6)

    def test_retired_hurt_is_not_a_team_wicket(self) -> None:
        self.assertEqual(self.rows[1]["pp_wickets"], 0)

    def test_outcome_is_from_batting_team_perspective(self) -> None:
        self.assertEqual(self.rows[0]["batting_team_won"], 1)
        self.assertEqual(self.rows[1]["batting_team_won"], 0)

    def test_short_fixture_is_flagged_incomplete(self) -> None:
        self.assertEqual(self.rows[0]["pp_complete"], 0)
        self.assertEqual(self.rows[1]["pp_complete"], 0)


if __name__ == "__main__":
    unittest.main()

