from __future__ import annotations

import sys
import unittest
import warnings
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


    def test_tradeoff_reference_encoder_drops_development_first_level(self) -> None:
        spec = ModelSpec(
            "reference", ("elo_difference",), ("venue", "toss_decision"),
            categorical_reference=True,
        )
        training = [
            {"elo_difference": value, "venue": venue, "toss_decision": decision,
             "batting_team_won": label}
            for value, venue, decision, label in (
                (-20, "Z", "field", 0), (-10, "A", "bat", 0),
                (10, "Z", "field", 1), (20, "A", "bat", 1),
            )
        ]
        model = fit_model(spec, training)
        preprocess = model.named_steps["preprocessing"]
        encoder = preprocess.named_transformers_["categorical"].named_steps["encoder"]
        self.assertEqual([levels.tolist() for levels in encoder.categories_],
                         [["A", "Z"], ["bat", "field"]])
        self.assertEqual(encoder.drop_idx_.tolist(), [0, 0])
        names = preprocess.get_feature_names_out().tolist()
        self.assertEqual(len(names), model.named_steps["classifier"].coef_.shape[1])
        self.assertIn("categorical__venue_Z", names)
        self.assertNotIn("categorical__venue_A", names)
        self.assertNotIn("categorical__toss_decision_bat", names)
        baseline, unknown = predict_model(
            spec, model,
            [{"elo_difference": 0, "venue": "A", "toss_decision": "bat"},
             {"elo_difference": 0, "venue": "unseen", "toss_decision": "bat"}],
        )
        self.assertAlmostEqual(baseline, unknown)
        self.assertEqual(names, fit_model(spec, list(reversed(training))).named_steps[
            "preprocessing"].get_feature_names_out().tolist())

    def test_reference_encoder_refits_only_on_sampled_development_rows(self) -> None:
        spec = ModelSpec("reference_sample", (), ("venue",), categorical_reference=True)
        first_sample = [
            {"venue": venue, "batting_team_won": outcome}
            for venue, outcome in (("A", 0), ("B", 1), ("A", 0), ("B", 1))
        ]
        second_sample = [
            {"venue": venue, "batting_team_won": outcome}
            for venue, outcome in (("B", 0), ("C", 1), ("B", 0), ("C", 1))
        ]
        first = fit_model(spec, first_sample)
        second = fit_model(spec, second_sample)
        first_encoder = first.named_steps["preprocessing"].named_transformers_[
            "categorical"].named_steps["encoder"]
        second_encoder = second.named_steps["preprocessing"].named_transformers_[
            "categorical"].named_steps["encoder"]
        self.assertEqual(first_encoder.categories_[0].tolist(), ["A", "B"])
        self.assertEqual(second_encoder.categories_[0].tolist(), ["B", "C"])
        self.assertEqual(first_encoder.drop_idx_.tolist(), [0])
        self.assertEqual(second_encoder.drop_idx_.tolist(), [0])
        self.assertNotIn("categorical__venue_A",
                         second.named_steps["preprocessing"].get_feature_names_out())

    def test_all_missing_numeric_feature_is_kept_without_imputer_warning(self) -> None:
        try:
            import sklearn  # noqa: F401
        except ImportError:
            self.skipTest("scikit-learn is not installed")

        spec = ModelSpec("all_missing", ("dew_expected",), ())
        training = [
            {"dew_expected": "", "batting_team_won": "1"},
            {"dew_expected": "", "batting_team_won": "0"},
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            model = fit_model(spec, training)

        probabilities = predict_model(
            spec,
            model,
            [{"dew_expected": ""}],
        )
        self.assertEqual(len(probabilities), 1)

if __name__ == "__main__":
    unittest.main()
