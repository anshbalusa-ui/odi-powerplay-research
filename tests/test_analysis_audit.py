from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.analysis_audit import audit_unlocked_model_rows  # noqa: E402


class FullCohortAuditTests(unittest.TestCase):
    def rows(self) -> list[dict[str, object]]:
        shared: dict[str, object] = {
            "match_id": "match-1",
            "match_date": "2023-06-01",
            "split": "development",
            "gender": "male",
            "match_type": "ODI",
            "analysis_eligible_primary": "1",
            "is_super_over": "0",
            "pp_runs": "50",
            "pp_wickets": "1",
            "pp_legal_balls": "60",
            "pp_delivery_events": "60",
            "pp_run_rate": "5.0",
            "pp_boundary_balls": "5",
            "pp_boundary_pct": "8.333333",
            "pp_dot_balls": "30",
            "pp_dot_ball_pct": "50.0",
            "pp_complete": "1",
            "balls_per_over": "6",
            "toss_decision": "bat",
            "venue": "Fixture Ground",
            "rule_era": "modern_2015_plus",
            "competition_type": "bilateral_series",
            "elo_difference": "0",
            "team_prior_matches": "10",
            "opponent_prior_matches": "10",
            "team_prior20_win_rate": "0.5",
            "opponent_prior20_win_rate": "0.5",
            "batting_team": "Alpha",
            "opponent": "Beta",
            "batting_first": "1",
            "batting_team_won_toss": "1",
            "year": "2023",
            "venue_history_available": "1",
            "venue_prior_matches": "5",
            "venue_prior_pp_runs_mean": "48",
            "venue_prior_pp_wickets_mean": "1",
            "venue_prior_boundary_pct": "10",
            "venue_prior_dot_ball_pct": "60",
        }
        return [
            {**shared, "innings_number": "1", "batting_team_won": "1"},
            {**shared, "innings_number": "2", "batting_team": "Beta",
             "opponent": "Alpha", "batting_first": "0", "batting_team_won": "0"},
            {
                "match_id": "locked-match",
                "match_date": "2025-06-01",
                "innings_number": "1",
                "split": "locked_test",
            },
            {
                "match_id": "locked-match",
                "match_date": "2025-06-01",
                "innings_number": "2",
                "split": "locked_test",
            },
        ]

    def test_audits_unlocked_metrics_and_keeps_locked_rows_structure_only(self) -> None:
        summary, issues = audit_unlocked_model_rows(self.rows())

        self.assertEqual(issues, [])
        self.assertFalse(summary["locked_test_outcomes_loaded"])
        self.assertEqual(summary["rows_by_split"], {"development": 2, "locked_test": 2})
        self.assertEqual(summary["unlocked_rows_checked_for_metrics"], 2)
        self.assertEqual(summary["powerplay_metric_audit"]["issue_count"], 0)

    def test_reports_ineligible_unlocked_row(self) -> None:
        rows = self.rows()
        rows[0]["pp_complete"] = "0"

        _, issues = audit_unlocked_model_rows(rows[:2])

        self.assertTrue(any(issue["field"] == "pp_complete" for issue in issues))

    def test_reports_unlocked_year_and_missing_predictor_counts(self) -> None:
        rows = self.rows()[:2]
        rows[0]["venue_prior_pp_runs_mean"] = ""
        summary, issues = audit_unlocked_model_rows(rows)
        self.assertEqual(issues, [])
        self.assertEqual(summary["unlocked_matches_by_year"], {"2023": 1})
        self.assertEqual(summary["missing_predictor_values_by_field"], {
            "venue_prior_pp_runs_mean": 1,
        })


    def test_rejects_two_winners_or_nonopposing_match_pair(self) -> None:
        rows = self.rows()[:2]
        rows[1]["batting_team_won"] = "1"
        rows[1]["batting_team"] = "Alpha"
        rows[1]["opponent"] = "Beta"
        rows[1]["match_date"] = "2023-06-02"
        _, issues = audit_unlocked_model_rows(rows)
        fields = {issue["field"] for issue in issues}
        self.assertIn("complementary_outcomes", fields)
        self.assertIn("opposing_teams", fields)
        self.assertIn("match_date_consistency", fields)

if __name__ == "__main__":
    unittest.main()
