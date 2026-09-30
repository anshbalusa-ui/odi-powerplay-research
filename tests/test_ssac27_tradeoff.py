from __future__ import annotations

import random
import unittest
from unittest.mock import patch
from odi_powerplay.modeling import predict_model

from odi_powerplay.tradeoff import (
    PRIMARY_INTERACTIONS,
    _fit_primary_model,
    _context_row,
    _paired_context_differences,
    _summaries,
    _prepare_rows,
    assert_unlocked_rows,
    draw_match_bootstrap_rows,
    local_support,
    solve_nonnegative_root,
)


class TradeoffBehaviorTests(unittest.TestCase):
    def test_support_is_stratified_by_wicket_and_uses_local_run_quantiles(self):
        rows = [
            {"match_id": "a", "batting_first": 1, "pp_wickets": 1, "elo_difference": 0.0, "venue_prior_pp_runs_mean": 40.0, "venue_history_available": 1, "pp_runs": 20.0},
            {"match_id": "b", "batting_first": 1, "pp_wickets": 1, "elo_difference": 0.1, "venue_prior_pp_runs_mean": 40.1, "venue_history_available": 1, "pp_runs": 30.0},
            {"match_id": "c", "batting_first": 1, "pp_wickets": 2, "elo_difference": 0.0, "venue_prior_pp_runs_mean": 40.0, "venue_history_available": 1, "pp_runs": 20.0},
            {"match_id": "d", "batting_first": 1, "pp_wickets": 2, "elo_difference": 0.1, "venue_prior_pp_runs_mean": 40.1, "venue_history_available": 1, "pp_runs": 30.0},
        ]
        support = local_support(
            rows, innings=1, wickets=1, elo=0.0, venue_runs=40.0,
            elo_mean=0.0, elo_sd=1.0, venue_mean=40.0, venue_sd=1.0,
            minimum_neighbors=2,
        )
        self.assertTrue(support["supported"])
        self.assertEqual(support["run_min"], 20.5)
        self.assertEqual(support["run_max"], 29.5)
        unsupported = local_support(
            rows, innings=1, wickets=3, elo=0.0, venue_runs=40.0,
            elo_mean=0.0, elo_sd=1.0, venue_mean=40.0, venue_sd=1.0,
            minimum_neighbors=2,
        )
        self.assertFalse(unsupported["supported"])
        self.assertIn("wicket", unsupported["reason"])

    def test_root_is_bounded_and_reports_no_bracket_as_undefined(self):
        root = solve_nonnegative_root(lambda runs: runs - 4.0, upper_delta=10.0)
        self.assertTrue(root["defined"])
        self.assertLessEqual(abs(root["delta"] - 4.0), 0.01)
        no_root = solve_nonnegative_root(lambda runs: runs + 1.0, upper_delta=10.0)
        self.assertFalse(no_root["defined"])
        self.assertEqual(no_root["reason"], "no_bracketed_nonnegative_root")

    def test_match_bootstrap_keeps_both_rows_and_duplicates_clusters(self):
        rows = [
            {"match_id": "a", "row": 1},
            {"match_id": "a", "row": 2},
            {"match_id": "b", "row": 3},
            {"match_id": "b", "row": 4},
        ]
        sampled = draw_match_bootstrap_rows(rows, sampled_match_ids=["a", "a"])
        self.assertEqual([row["row"] for row in sampled], [1, 2, 1, 2])

    def test_reference_predictions_include_development_scaled_interactions(self):
        dev = [
            {"pp_runs": 20, "pp_wickets": 1, "batting_first": 0,
             "elo_difference": -50, "venue_prior_pp_runs_mean": 35},
            {"pp_runs": 60, "pp_wickets": 3, "batting_first": 1,
             "elo_difference": 50, "venue_prior_pp_runs_mean": 55},
        ]
        prepared, _, decisions = _prepare_rows(dev, dev=dev, interactions=PRIMARY_INTERACTIONS)
        context = {**dev[0], "interaction_operand_mean_sd": decisions["interaction_operand_mean_sd"]}
        predicted = _context_row(context, runs=20, wickets=1, innings=0,
                                 elo=-50, venue_runs=35)
        for index in range(len(PRIMARY_INTERACTIONS)):
            self.assertEqual(predicted[f"_interaction_{index}"],
                             prepared[0][f"_interaction_{index}"])
    def test_missing_interaction_operand_uses_development_median(self):
        dev = [
            {"pp_runs": 20, "pp_wickets": 1, "batting_first": 0,
             "elo_difference": -20, "venue_prior_pp_runs_mean": 30},
            {"pp_runs": 80, "pp_wickets": 2, "batting_first": 1,
             "elo_difference": 20, "venue_prior_pp_runs_mean": None},
            {"pp_runs": 40, "pp_wickets": 3, "batting_first": 1,
             "elo_difference": 0, "venue_prior_pp_runs_mean": 50},
            {"pp_runs": 60, "pp_wickets": 0, "batting_first": 0,
             "elo_difference": 10, "venue_prior_pp_runs_mean": 90},
        ]
        prepared, _, decisions = _prepare_rows(
            dev, dev=dev, interactions=PRIMARY_INTERACTIONS)
        run_mean, run_sd = decisions["interaction_operand_mean_sd"]["pp_runs"]
        venue_mean, venue_sd = decisions["interaction_operand_mean_sd"][
            "venue_prior_pp_runs_mean"]
        expected = ((80 - run_mean) / run_sd) * (
            decisions["interaction_operand_medians"]["venue_prior_pp_runs_mean"]
            - venue_mean
        ) / venue_sd
        self.assertAlmostEqual(prepared[1]["_interaction_4"], expected)
        self.assertNotEqual(prepared[1]["_interaction_4"], 0.0)

    def test_interaction_alias_with_existing_run_column_fails_development_gate(self):
        development = [
            {"pp_runs": runs, "batting_first": 1}
            for runs in (20, 28, 37, 49, 61, 72, 85)
        ]
        with self.assertRaisesRegex(ValueError, "rank_deficient_development_interactions"):
            _prepare_rows(development, dev=development,
                          interactions=(("pp_runs", "batting_first"),),
                          enforce_interaction_rank=True)


    def test_three_knot_spline_has_natural_tail_and_rejects_rank_deficiency(self):
        dev = [{"pp_runs": value} for value in (0, 10, 20, 30, 40, 50)]
        prepared, spec, _ = _prepare_rows(
            dev, dev=dev, interactions=(), spline_knots=(10, 20, 30))
        self.assertIn("_spline_1", spec.numeric_features)
        self.assertNotIn("_spline_2", spec.numeric_features)
        tail = [row["_spline_1"] for row in prepared[-3:]]
        self.assertAlmostEqual(tail[2] - tail[1], tail[1] - tail[0])
        with self.assertRaisesRegex(ValueError, "rank_deficient_development_spline"):
            _prepare_rows([{"pp_runs": x} for x in (0, 1, 2, 3)],
                          dev=[{"pp_runs": x} for x in (0, 1, 2, 3)],
                          interactions=(), spline_knots=(10, 20, 30))

    def test_primary_fit_is_invariant_to_interleaved_2024_labels(self):
        base = {
            "team_prior_matches": 10, "opponent_prior_matches": 10,
            "team_prior20_win_rate": 0.5, "opponent_prior20_win_rate": 0.5,
            "batting_team_won_toss": 1, "venue_history_available": 1,
            "venue_prior_matches": 4, "venue_prior_pp_wickets_mean": 1.5,
            "venue": "Ground", "rule_era": "modern_2015_plus",
            "competition_type": "bilateral_series", "toss_decision": "bat",
            "year": 2023, "split": "development",
        }
        rng = random.Random(817)
        development = [
            {**base, "pp_runs": rng.randrange(18, 91),
             "pp_wickets": rng.randrange(4), "batting_first": rng.randrange(2),
             "elo_difference": rng.randrange(-85, 86),
             "venue_prior_pp_runs_mean": rng.randrange(29, 75),
             "batting_team_won": index % 2}
            for index in range(64)
        ]
        validation = [
            {**base, "split": "validation", "year": 2024, "pp_runs": 95,
             "pp_wickets": 0, "batting_first": 1,
             "elo_difference": 0, "venue_prior_pp_runs_mean": 55,
             "batting_team_won": label}
            for label in (1, 0)
        ]
        spec_a, model_a, _ = _fit_primary_model([*validation, *development])
        reversed_labels = [{**row, "batting_team_won": 1-row["batting_team_won"]}
                           for row in validation]
        spec_b, model_b, _ = _fit_primary_model([*development, *reversed_labels])
        prepared, _, _ = _prepare_rows(
            development, dev=development, interactions=PRIMARY_INTERACTIONS)
        self.assertAlmostEqual(
            predict_model(spec_a, model_a, prepared[:1])[0],
            predict_model(spec_b, model_b, prepared[:1])[0],
            places=12,
        )

    def test_target_wicket_envelope_alone_bounds_supported_root_path(self):
        rows = []
        for wickets, high in ((1, 50), (2, 70)):
            for index in range(20):
                rows.append({
                    "match_id": f"{wickets}-{index}", "batting_first": 1,
                    "pp_wickets": wickets, "pp_runs": 47 if index < 10 else high,
                    "elo_difference": -0.1 if index % 2 else 0.1,
                    "venue_prior_pp_runs_mean": 39.9 if index % 2 else 40.1,
                    "venue_history_available": 1, "batting_team_won_toss": 0,
                    "venue": "Ground", "rule_era": "modern_2015_plus",
                    "competition_type": "bilateral_series", "toss_decision": "bat",
                })
        context = {
            "venue": "Ground", "rule_era": "modern_2015_plus",
            "competition_type": "bilateral_series", "toss_decision": "bat",
            "batting_team_won_toss": 0, "elo_states": [0.0] * 3,
            "elo_mean": 0.0, "elo_sd": 1.0, "venue_states": [40.0] * 3,
            "run_reference": 47, "interaction_operand_mean_sd": {},
        }
        probability = lambda row: 0.3 + .01 * row["pp_runs"] - .13 * row["pp_wickets"]
        with patch("odi_powerplay.tradeoff._prob",
                   side_effect=lambda _spec, _model, row: probability(row)), patch(
            "odi_powerplay.tradeoff.predict_model",
            side_effect=lambda _spec, _model, batch: [probability(row) for row in batch]
        ):
            cells, _ = _summaries(rows, context, None, None, PRIMARY_INTERACTIONS)
        first = next(cell for cell in cells if cell["contrast"] == "primary_1_to_2"
                     and cell["innings"] == 1)
        self.assertLess(first["support_start"]["run_max"], 60)
        self.assertGreater(first["support_target"]["run_max"], 60)
        self.assertTrue(first["defined"])
        self.assertAlmostEqual(first["runs_per_wicket"], 13, delta=0.01)

    def test_starting_run_must_be_inside_both_wicket_strata(self):
        rows = [
            {
                "match_id": f"{wickets}-{index}", "batting_first": 1,
                "pp_wickets": wickets, "pp_runs": 20 + index % 5,
                "elo_difference": (-1) ** index * .1,
                "venue_prior_pp_runs_mean": 40 + (-1) ** index * .1,
                "venue_history_available": 1, "batting_team_won_toss": 0,
                "venue": "Ground", "rule_era": "modern_2015_plus",
                "competition_type": "bilateral_series", "toss_decision": "bat",
            }
            for wickets in (1, 2) for index in range(20)
        ]
        context = {
            "venue": "Ground", "rule_era": "modern_2015_plus",
            "competition_type": "bilateral_series", "toss_decision": "bat",
            "batting_team_won_toss": 0, "elo_states": [0.0] * 3,
            "elo_mean": 0.0, "elo_sd": 1.0, "venue_states": [40.0] * 3,
            "run_reference": 100, "interaction_operand_mean_sd": {},
        }
        cells, _ = _summaries(rows, context, None, None, PRIMARY_INTERACTIONS)
        for cell in (row for row in cells if row["contrast"] == "primary_1_to_2"
                     and row["innings"] == 1):
            self.assertEqual(cell["reason"], "starting_run_outside_supported_envelope")
            self.assertNotIn("probability_difference_fixed_run", cell)
            self.assertFalse(cell["defined"])

    def test_paired_context_intervals_use_identical_refit_and_count_undefined_roots(self):
        cells = [
            {
                "innings": innings, "elo_state": elo, "venue_state": venue,
                "wickets_from": 1, "contrast": "primary_1_to_2",
                "probability_difference_fixed_run": -.1,
                "runs_per_wicket": (14 if venue == 2 else 12)
                if (innings, elo, venue) in ((1, 3, 2), (1, 3, 3)) else None,
                "defined": (innings, elo, venue) in ((1, 3, 2), (1, 3, 3)),
                "reason": None if (innings, elo, venue) in ((1, 3, 2), (1, 3, 3))
                          else "no_bracketed_nonnegative_root",
            }
            for innings in (1, 0) for elo in (1, 2, 3) for venue in (1, 2, 3)
        ]
        def key(innings, elo, venue):
            return innings, elo, venue, 1, "primary_1_to_2"
        replicate_1 = {
            key(1, 2, 2): {"fixed_run_probability_difference": .2},
            key(0, 2, 2): {"fixed_run_probability_difference": .1},
            key(1, 3, 2): {"fixed_run_probability_difference": .2,
                            "runs_per_wicket": 16},
            key(1, 3, 3): {"fixed_run_probability_difference": .1,
                            "runs_per_wicket": 13},
        }
        replicate_2 = {
            key(1, 2, 2): {"fixed_run_probability_difference": .8},
            key(0, 2, 2): {"fixed_run_probability_difference": .7},
            key(1, 3, 2): {"fixed_run_probability_difference": .8,
                            "runs_per_wicket": 15},
            key(1, 3, 3): {"fixed_run_probability_difference": .7},
        }
        records = _paired_context_differences(
            cells, [replicate_1, replicate_2], min_root_valid_fraction=.8)
        self.assertEqual(len(records), 90)
        innings_difference = next(
            record for record in records
            if record["axis"] == "innings"
            and record["quantity"] == "fixed_run_probability_difference"
            and record["context_a"] == {"innings": 1, "elo_state": 2, "venue_state": 2}
            and record["context_b"] == {"innings": 0, "elo_state": 2, "venue_state": 2}
        )
        self.assertEqual(innings_difference["requested_replicates"], 2)
        self.assertEqual(innings_difference["valid_paired_replicates"], 2)
        self.assertAlmostEqual(innings_difference["lower_95"], .1)
        self.assertAlmostEqual(innings_difference["upper_95"], .1)
        root_difference = next(
            record for record in records
            if record["axis"] == "venue"
            and record["quantity"] == "runs_per_wicket"
            and record["context_a"] == {"innings": 1, "elo_state": 3, "venue_state": 2}
            and record["context_b"] == {"innings": 1, "elo_state": 3, "venue_state": 3}
        )
        self.assertEqual(root_difference["valid_paired_replicates"], 1)
        self.assertEqual(root_difference["undefined_replicates"], 1)
        self.assertIsNone(root_difference["lower_95"])
        self.assertIsNone(root_difference["upper_95"])
        complete_second = {
            **replicate_2,
            key(1, 3, 3): {
                "fixed_run_probability_difference": .7, "runs_per_wicket": 11
            },
        }
        complete_records = _paired_context_differences(
            cells, [replicate_1, complete_second], min_root_valid_fraction=.8)
        complete_root = next(
            record for record in complete_records
            if record["axis"] == "venue"
            and record["quantity"] == "runs_per_wicket"
            and record["context_a"] == root_difference["context_a"]
            and record["context_b"] == root_difference["context_b"]
        )
        self.assertEqual(complete_root["valid_paired_replicates"], 2)
        self.assertAlmostEqual(complete_root["estimate"], 2)
        self.assertAlmostEqual(complete_root["lower_95"], 3.025)
        self.assertAlmostEqual(complete_root["upper_95"], 3.975)

    def test_unlocked_guard_rejects_locked_period_without_reading_outcome(self):
        assert_unlocked_rows([{"match_date": "2024-12-31", "split": "validation"}])
        with self.assertRaisesRegex(ValueError, "locked"):
            assert_unlocked_rows([{"match_date": "2025-01-01", "split": "locked_test"}])
        for date, split in (("", "development"), ("2024-04-01", "development"),
                            ("2023-06-01", "validation")):
            with self.subTest(date=date, split=split), self.assertRaises(ValueError):
                assert_unlocked_rows([{"match_date": date, "split": split}])


if __name__ == "__main__":
    unittest.main()
