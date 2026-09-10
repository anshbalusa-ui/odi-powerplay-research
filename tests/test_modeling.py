from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.model_table import FORBIDDEN_PREDICTORS
from odi_powerplay.modeling import (
    ModelSpec,
    fit_model,
    make_model_specs,
    partition_chronological_rows,
    predict_model,
    rolling_origin_splits,
    validate_model_specs,
)


class LockedRow(dict):
    def __getitem__(self, key):
        if key == "batting_team_won":
            raise AssertionError("Locked-test outcome was read")
        return super().__getitem__(key)


class ModelingTests(unittest.TestCase):
    def test_default_specs_are_nested_and_leakage_free(self) -> None:
        specs = {spec.name: spec for spec in make_model_specs()}
        validate_model_specs(specs.values(), forbidden=FORBIDDEN_PREDICTORS)
        self.assertTrue(
            set(specs["m0_pre_match"].all_features)
            < set(specs["m1_context_powerplay"].all_features)
        )
        venue_features = {
            "venue_history_available",
            "venue_prior_matches",
            "venue_prior_pp_runs_mean",
            "venue_prior_pp_wickets_mean",
            "venue_prior_boundary_pct",
            "venue_prior_dot_ball_pct",
        }
        self.assertTrue(
            venue_features <= set(specs["venue_history_powerplay_sensitivity"].numeric_features)
        )
        self.assertTrue(venue_features.isdisjoint(specs["m1_context_powerplay"].numeric_features))
        self.assertEqual(
            set(specs["m2_prespecified_interactions"].interaction_features),
            {("pp_runs", "batting_first"), ("pp_wickets", "batting_first")},
        )
        process_features = set(specs["scoring_process_sensitivity"].all_features)
        self.assertTrue({"pp_wickets", "pp_boundary_pct", "pp_dot_ball_pct"} <= process_features)
        self.assertNotIn("pp_runs", process_features)
        self.assertEqual(specs["random_forest_challenger"].estimator, "random_forest")
        self.assertEqual(specs["xgboost_challenger"].estimator, "xgboost")

    def test_specs_reject_outcomes_and_duplicate_run_measure(self) -> None:
        with self.assertRaisesRegex(ValueError, "Forbidden predictors"):
            validate_model_specs(
                [ModelSpec("leaked", ("winner",), ())], forbidden=FORBIDDEN_PREDICTORS
            )
        with self.assertRaisesRegex(ValueError, "deterministic"):
            validate_model_specs(
                [ModelSpec("duplicate", ("pp_runs", "pp_run_rate"), ())],
                forbidden=FORBIDDEN_PREDICTORS,
            )

    def test_partition_never_reads_locked_outcome(self) -> None:
        rows = [
            {"split": "development", "match_id": "d", "batting_team_won": "1"},
            {"split": "validation", "match_id": "v", "batting_team_won": "0"},
            LockedRow(split="locked_test", match_id="t", batting_team_won="1"),
        ]
        development, validation, locked_ids = partition_chronological_rows(rows)
        self.assertEqual([row["match_id"] for row in development], ["d"])
        self.assertEqual([row["match_id"] for row in validation], ["v"])
        self.assertEqual(locked_ids, ["t"])

    def test_rolling_origin_uses_only_earlier_complete_matches(self) -> None:
        rows = [
            {"match_id": str(year), "match_date": f"{year}-06-01"}
            for year in (2019, 2020, 2021, 2022)
            for _innings in (1, 2)
        ]
        folds = rolling_origin_splits(rows, validation_years=(2021, 2022))
        self.assertEqual(len(folds), 2)
        for training, validation in folds:
            validation_year = int(validation[0]["match_date"][:4])
            self.assertTrue(all(int(row["match_date"][:4]) < validation_year for row in training))
            self.assertTrue(
                all(int(row["match_date"][:4]) == validation_year for row in validation)
            )
            self.assertTrue(
                {row["match_id"] for row in training}.isdisjoint(
                    {row["match_id"] for row in validation}
                )
            )

    def test_logistic_pipeline_handles_missing_and_unseen_values(self) -> None:
        try:
            import sklearn  # noqa: F401
        except ImportError:
            self.skipTest("scikit-learn is not installed")

        spec = ModelSpec("small", ("elo_difference",), ("venue",))
        training = [
            {"elo_difference": "10", "venue": "A", "batting_team_won": "1"},
            {"elo_difference": "-10", "venue": "B", "batting_team_won": "0"},
            {"elo_difference": "", "venue": "A", "batting_team_won": "1"},
            {"elo_difference": "-5", "venue": "B", "batting_team_won": "0"},
        ]
        model = fit_model(spec, training)
        probabilities = predict_model(
            spec,
            model,
            [{"elo_difference": "3", "venue": "previously unseen"}],
        )
        self.assertEqual(len(probabilities), 1)
        self.assertGreaterEqual(probabilities[0], 0.0)
        self.assertLessEqual(probabilities[0], 1.0)


if __name__ == "__main__":
    unittest.main()
