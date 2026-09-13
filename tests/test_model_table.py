from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.model_table import (
    assign_split,
    build_model_table,
    merge_strength_into_innings,
    merge_venue_conditions_into_innings,
    validate_feature_allowlist,
)


class ModelTableTests(unittest.TestCase):
    def innings_rows(self) -> list[dict[str, object]]:
        shared = {
            "match_id": "match-1",
            "match_date": "2024-06-01",
            "venue": "Fixture Ground",
        }
        return [
            {
                **shared,
                "innings_number": 1,
                "batting_team": "A",
                "opponent": "B",
                "batting_team_won": 1,
                "pp_runs": 55,
            },
            {
                **shared,
                "innings_number": 2,
                "batting_team": "B",
                "opponent": "A",
                "batting_team_won": 0,
                "pp_runs": 42,
            },
        ]

    def strength_rows(self) -> list[dict[str, object]]:
        return [
            {
                "match_id": "match-1",
                "match_date": "2024-06-01",
                "team_1": "A",
                "team_2": "B",
                "team_1_elo_pre": 1525.0,
                "team_2_elo_pre": 1475.0,
                "elo_difference_team_1": 50.0,
                "team_1_prior_matches": 30,
                "team_2_prior_matches": 28,
                "team_1_prior20_win_rate": 0.65,
                "team_2_prior20_win_rate": 0.4,
            }
        ]

    def venue_rows(self) -> list[dict[str, object]]:
        return [
            {
                "match_id": "match-1",
                "match_date": "2024-06-01",
                "venue": "Fixture Ground",
                "venue_history_available": 1,
                "venue_prior_matches": 10,
                "venue_prior_innings": 20,
                "venue_prior_pp_runs_mean": 48.5,
                "venue_prior_pp_wickets_mean": 1.4,
                "venue_prior_boundary_pct": 11.2,
                "venue_prior_dot_ball_pct": 65.0,
            }
        ]

    def test_maps_strength_to_each_batting_team_perspective(self) -> None:
        merged = merge_strength_into_innings(self.innings_rows(), self.strength_rows())
        self.assertEqual(merged[0]["team_elo_pre"], 1525.0)
        self.assertEqual(merged[0]["elo_difference"], 50.0)
        self.assertEqual(merged[1]["team_elo_pre"], 1475.0)
        self.assertEqual(merged[1]["opponent_elo_pre"], 1525.0)
        self.assertEqual(merged[1]["elo_difference"], -50.0)
        self.assertEqual(merged[1]["team_prior20_win_rate"], 0.4)

    def test_split_boundaries_are_chronological(self) -> None:
        self.assertEqual(assign_split("2023-12-31"), "development")
        self.assertEqual(assign_split("2024-01-01"), "validation")
        self.assertEqual(assign_split("2024-12-31"), "validation")
        self.assertEqual(assign_split("2025-01-01"), "locked_test")

    def test_complete_model_table_keeps_match_in_one_split(self) -> None:
        table = build_model_table(self.innings_rows(), self.strength_rows(), self.venue_rows())
        self.assertEqual({row["split"] for row in table}, {"validation"})
        self.assertEqual({row["pitch_available"] for row in table}, {0})
        timing_fields = {
            "scheduled_start_local",
            "timezone_name",
            "scheduled_start_utc",
            "start_time_status",
        }
        self.assertTrue(timing_fields.isdisjoint(table[0]))

    def test_feature_allowlist_rejects_outcomes_and_missing_fields(self) -> None:
        table = build_model_table(self.innings_rows(), self.strength_rows(), self.venue_rows())
        validate_feature_allowlist(table, ["pp_runs", "elo_difference"])
        with self.assertRaisesRegex(ValueError, "Forbidden predictors"):
            validate_feature_allowlist(table, ["batting_team_won"])
        with self.assertRaisesRegex(ValueError, "Forbidden predictors"):
            validate_feature_allowlist(table, ["scheduled_start_utc"])
        with self.assertRaisesRegex(ValueError, "missing from model table"):
            validate_feature_allowlist(table, ["future_feature"])

    def test_duplicate_strength_rows_are_rejected(self) -> None:
        duplicated = [*self.strength_rows(), *self.strength_rows()]
        with self.assertRaisesRegex(ValueError, "Duplicate strength row"):
            merge_strength_into_innings(self.innings_rows(), duplicated)

    def test_venue_conditions_join_to_both_innings_and_validate_identity(self) -> None:
        merged = merge_venue_conditions_into_innings(
            self.innings_rows(),
            self.venue_rows(),
        )
        self.assertEqual(
            {row["venue_prior_pp_runs_mean"] for row in merged},
            {48.5},
        )

        mismatched = [{**self.venue_rows()[0], "venue": "Different Ground"}]
        with self.assertRaisesRegex(ValueError, "venue mismatch"):
            merge_venue_conditions_into_innings(self.innings_rows(), mismatched)


if __name__ == "__main__":
    unittest.main()
