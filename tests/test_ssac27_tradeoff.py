from __future__ import annotations

import unittest
from odi_powerplay.modeling import predict_model

from odi_powerplay.tradeoff import (
    PRIMARY_INTERACTIONS,
    _fit_primary_model,
    _context_row,
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
        development = [
            {**base, "pp_runs": r, "pp_wickets": w, "batting_first": b,
             "elo_difference": e, "venue_prior_pp_runs_mean": v,
             "batting_team_won": y}
            for r, w, b, e, v, y in (
                (24, 0, 1, -70, 35, 1), (41, 1, 0, 0, 45, 0),
                (56, 2, 1, 70, 55, 1), (78, 3, 0, -20, 50, 0),
            )
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
