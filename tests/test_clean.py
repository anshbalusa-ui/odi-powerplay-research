from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.clean import clean_rows, exclusion_reasons, select_pilot  # noqa: E402


def row(**updates):
    base = {
        "match_id": "m1",
        "match_date": "2023-10-05",
        "year": 2023,
        "event_name": "ICC Cricket World Cup",
        "gender": "male",
        "venue": "Example Ground",
        "city": None,
        "batting_team": "Alpha",
        "opponent": "Beta",
        "innings_number": 1,
        "toss_winner": "Beta",
        "toss_decision": "field",
        "match_status": "decided",
        "result_method": None,
        "batting_team_won": 1,
        "pp_complete": 1,
    }
    base.update(updates)
    return base


class CleaningTests(unittest.TestCase):
    def test_clean_decided_two_innings_match_is_retained(self) -> None:
        rows = [row(), row(batting_team="Beta", opponent="Alpha", innings_number=2, batting_team_won=0)]
        cleaned, audit, excluded = clean_rows(rows)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(audit[0]["analysis_eligible_core"], 1)
        self.assertEqual(excluded, [])
        self.assertTrue(all(item["city"] == "Unknown" for item in cleaned))
        self.assertTrue(all(item["city_missing"] == 1 for item in cleaned))
        self.assertTrue(all(item["result_method"] == "none" for item in cleaned))
        self.assertTrue(all(item["exclusion_reasons"] == "none" for item in cleaned))

    def test_undecided_incomplete_and_dls_reasons_accumulate(self) -> None:
        rows = [
            row(match_status="no_result", result_method="D/L", pp_complete=0, batting_team_won=None),
            row(
                batting_team="Beta",
                opponent="Alpha",
                innings_number=2,
                match_status="no_result",
                result_method="D/L",
                pp_complete=0,
                batting_team_won=None,
            ),
        ]
        self.assertEqual(
            exclusion_reasons(rows),
            ["NO_RESULT", "DLS_OR_REVISED_TARGET", "INCOMPLETE_POWERPLAY"],
        )

    def test_one_innings_match_is_excluded(self) -> None:
        cleaned, _, excluded = clean_rows([row()])
        self.assertEqual(cleaned, [])
        self.assertIn("NOT_TWO_REGULATION_INNINGS", excluded[0]["exclusion_reasons"])

    def test_inconsistent_outcomes_are_excluded(self) -> None:
        rows = [row(), row(batting_team="Beta", opponent="Alpha", innings_number=2)]
        self.assertIn("INCONSISTENT_OUTCOME_LABELS", exclusion_reasons(rows))

    def test_pilot_selector_uses_year_gender_and_event(self) -> None:
        candidates = [
            row(),
            row(match_id="m2", year=2019, event_name="World Cup"),
            row(match_id="m3", year=2022),
            row(match_id="m4", gender="female"),
            row(match_id="m5", event_name="ICC Cricket World Cup Qualifier"),
        ]
        selected = select_pilot(candidates)
        self.assertEqual([item["match_id"] for item in selected], ["m1", "m2"])


if __name__ == "__main__":
    unittest.main()
