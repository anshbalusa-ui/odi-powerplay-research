from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.evaluation import (
    calibration_coefficients,
    calibration_table,
    cluster_bootstrap_calibration,
    cluster_bootstrap_metrics,
    compute_metrics,
    draw_cluster_indices,
    roc_auc,
)


class EvaluationTests(unittest.TestCase):
    def test_perfect_probabilities_have_perfect_metrics(self) -> None:
        metrics = compute_metrics([0, 1], [0.0, 1.0])
        self.assertEqual(metrics["brier_score"], 0.0)
        self.assertLess(metrics["log_loss"], 1e-12)
        self.assertEqual(metrics["roc_auc"], 1.0)
        self.assertEqual(metrics["accuracy_at_0_5"], 1.0)

    def test_calibration_coefficients_are_finite_for_varying_predictions(self) -> None:
        result = calibration_coefficients(
            [0, 0, 1, 0, 1, 1],
            [0.1, 0.3, 0.55, 0.6, 0.7, 0.9],
        )
        self.assertIsNotNone(result["calibration_intercept"])
        self.assertIsNotNone(result["calibration_slope"])

    def test_constant_predictions_have_unidentifiable_calibration_slope(self) -> None:
        result = calibration_coefficients([0, 1], [0.5, 0.5])
        self.assertIsNone(result["calibration_intercept"])
        self.assertIsNone(result["calibration_slope"])

    def test_auc_handles_tied_probabilities(self) -> None:
        self.assertEqual(roc_auc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5)

    def test_cluster_sampling_keeps_both_innings_together(self) -> None:
        clusters = ["m1", "m1", "m2", "m2", "m3", "m3"]
        indices = draw_cluster_indices(clusters, random_generator=random.Random(7))
        counts = {index: indices.count(index) for index in range(len(clusters))}
        self.assertEqual(counts[0], counts[1])
        self.assertEqual(counts[2], counts[3])
        self.assertEqual(counts[4], counts[5])

    def test_bootstrap_is_reproducible_and_reports_failures(self) -> None:
        predictions = [
            {"match_id": "m1", "label": 1, "probability": 0.8},
            {"match_id": "m1", "label": 0, "probability": 0.2},
            {"match_id": "m2", "label": 1, "probability": 0.7},
            {"match_id": "m2", "label": 0, "probability": 0.3},
        ]
        first = cluster_bootstrap_metrics(predictions, repetitions=20, seed=5)
        second = cluster_bootstrap_metrics(predictions, repetitions=20, seed=5)
        self.assertEqual(first, second)
        self.assertEqual(first["repetitions_valid"], 20)

    def test_calibration_bootstrap_is_clustered_and_reproducible(self) -> None:
        predictions = [
            {"match_id": "m1", "label": 1, "probability": 0.8},
            {"match_id": "m1", "label": 0, "probability": 0.2},
            {"match_id": "m2", "label": 1, "probability": 0.7},
            {"match_id": "m2", "label": 0, "probability": 0.3},
        ]
        first = cluster_bootstrap_calibration(predictions, bins=2, repetitions=20, seed=5)
        second = cluster_bootstrap_calibration(predictions, bins=2, repetitions=20, seed=5)
        self.assertEqual(first, second)
        self.assertTrue(all(row["bootstrap_repetitions_valid"] > 0 for row in first))

    def test_calibration_table_retains_every_prediction(self) -> None:
        table = calibration_table([0, 1, 1], [0.1, 0.7, 1.0], bins=5)
        self.assertEqual(sum(int(row["count"]) for row in table), 3)
        self.assertEqual(table[-1]["bin"], 4)


if __name__ == "__main__":
    unittest.main()
