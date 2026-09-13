from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.quality import audit_powerplay_rows


class PowerplayQualityTests(unittest.TestCase):
    def valid_rows(self) -> list[dict[str, object]]:
        shared = {
            "match_id": "match-1",
            "pp_runs": 48,
            "pp_wickets": 2,
            "pp_legal_balls": 60,
            "pp_delivery_events": 63,
            "pp_run_rate": 4.8,
            "pp_boundary_balls": 6,
            "pp_boundary_pct": 10.0,
            "pp_dot_balls": 30,
            "pp_dot_ball_pct": 50.0,
            "pp_complete": 1,
            "balls_per_over": 6,
        }
        return [
            {**shared, "innings_number": 1, "batting_team_won": 1},
            {**shared, "innings_number": 2, "batting_team_won": 0},
        ]

    def test_accepts_consistent_powerplay_and_match_metrics(self) -> None:
        summary, issues = audit_powerplay_rows(self.valid_rows())
        self.assertEqual(summary["rows_checked"], 2)
        self.assertEqual(summary["matches_checked"], 1)
        self.assertEqual(summary["issue_count"], 0)
        self.assertEqual(issues, [])

    def test_reports_each_corrupted_requested_metric(self) -> None:
        rows = self.valid_rows()
        rows[0].update(
            {
                "pp_runs": -1,
                "pp_wickets": 11,
                "pp_boundary_pct": 9.0,
                "pp_dot_ball_pct": 49.0,
            }
        )
        summary, issues = audit_powerplay_rows(rows)
        fields = {issue["field"] for issue in issues}
        self.assertGreater(summary["issue_count"], 0)
        self.assertTrue(
            {"pp_runs", "pp_wickets", "pp_boundary_pct", "pp_dot_ball_pct"}.issubset(fields)
        )

    def test_reports_broken_match_pairing(self) -> None:
        summary, issues = audit_powerplay_rows(self.valid_rows()[:1])
        self.assertEqual(summary["matches_checked"], 1)
        self.assertIn("match_row_count", {issue["field"] for issue in issues})


if __name__ == "__main__":
    unittest.main()
