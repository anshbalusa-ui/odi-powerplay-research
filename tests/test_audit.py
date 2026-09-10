from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.audit import build_hand_audit_template, select_hand_audit_rows


class HandAuditTests(unittest.TestCase):
    def fixture_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for year in (2015, 2016, 2017):
            for match_number in range(4):
                match_id = f"{year}-{match_number}"
                for innings_number in (1, 2):
                    rows.append(
                        {
                            "match_id": match_id,
                            "match_date": f"{year}-01-01",
                            "year": year,
                            "event_name": "Fixture Series",
                            "venue": "Fixture Ground",
                            "batting_team": f"Team {innings_number}",
                            "opponent": f"Team {3 - innings_number}",
                            "innings_number": innings_number,
                            "pp_runs": 40,
                            "pp_wickets": 1,
                            "pp_legal_balls": 60,
                            "pp_boundary_balls": 5,
                            "pp_boundary_pct": 8.333333,
                            "pp_dot_balls": 35,
                            "pp_dot_ball_pct": 58.333333,
                            "toss_winner": "Team 1",
                            "toss_decision": "bat",
                            "batting_team_won": int(innings_number == 1),
                        }
                    )
        return rows

    def test_sample_is_deterministic_stratified_and_keeps_match_pairs(self) -> None:
        rows = self.fixture_rows()
        first = select_hand_audit_rows(rows, minimum_innings=8, seed="fixed")
        second = select_hand_audit_rows(reversed(rows), minimum_innings=8, seed="fixed")
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first), 8)
        self.assertEqual({int(row["year"]) for row in first}, {2015, 2016, 2017})
        counts = {match_id: 0 for match_id in {str(row["match_id"]) for row in first}}
        for row in first:
            counts[str(row["match_id"])] += 1
        self.assertEqual(set(counts.values()), {2})

    def test_template_separates_extracted_and_audited_values(self) -> None:
        sampled = select_hand_audit_rows(self.fixture_rows(), minimum_innings=2)
        template = build_hand_audit_template(sampled)
        self.assertEqual(template[0]["extracted_pp_runs"], 40)
        self.assertEqual(template[0]["audited_pp_runs"], "")
        self.assertTrue(str(template[0]["source_json"]).endswith(".json"))


if __name__ == "__main__":
    unittest.main()
