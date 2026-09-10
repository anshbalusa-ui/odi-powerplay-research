from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.clean import (  # noqa: E402
    classify_competition,
    clean_rows,
    exclusion_reasons,
    select_primary_cohort,
    select_world_cup_subgroup,
)


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

    def test_primary_selector_uses_gender_but_keeps_all_available_odi_years_and_events(self) -> None:
        candidates = [
            row(),
            row(match_id="m2", year=2019, event_name="Pakistan in Australia ODI Series"),
            row(match_id="m3", year=2014),
            row(match_id="m4", gender="female"),
            row(match_id="m5", event_name="ICC Cricket World Cup Qualifier"),
        ]
        selected = select_primary_cohort(candidates)
        self.assertEqual([item["match_id"] for item in selected], ["m1", "m2", "m3", "m5"])
        self.assertTrue(all(item["analysis_eligible_primary"] == 1 for item in selected))
        self.assertEqual(next(item for item in selected if item["match_id"] == "m3")["rule_era"], "historical_pre_2015")

    def test_explicit_start_year_can_still_create_modern_sensitivity_cohort(self) -> None:
        candidates = [row(match_id="old", year=2014), row(match_id="modern", year=2015)]
        selected = select_primary_cohort(candidates, start_year=2015)
        self.assertEqual([item["match_id"] for item in selected], ["modern"])

    def test_competition_labels_distinguish_world_cup_from_qualifier(self) -> None:
        self.assertEqual(classify_competition("ICC Cricket World Cup"), "world_cup")
        self.assertEqual(
            classify_competition("ICC Cricket World Cup Qualifier"),
            "qualification_pathway",
        )
        self.assertEqual(
            classify_competition("ICC Men's Cricket World Cup Super League"),
            "qualification_pathway",
        )
        self.assertEqual(
            classify_competition("Asia Cup Qualifier"),
            "qualification_pathway",
        )
        self.assertEqual(
            classify_competition("Pakistan in Australia ODI Series"),
            "bilateral_series",
        )

    def test_world_cup_is_only_a_subgroup_of_primary_rows(self) -> None:
        primary = select_primary_cohort(
            [row(), row(match_id="m2", event_name="Pakistan in Australia ODI Series")]
        )
        subgroup = select_world_cup_subgroup(primary)
        self.assertEqual([item["match_id"] for item in subgroup], ["m1"])


if __name__ == "__main__":
    unittest.main()
