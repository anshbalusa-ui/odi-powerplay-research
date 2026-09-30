"""Model agreement is a stability diagnostic, not pitch truth."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from odi_powerplay.pitch_expectation import pairwise_agreement, audit_sample  # noqa: E402
from build_pitch_expectation_consensus import cross_model_consensus_summary  # noqa: E402


class AgreementTests(unittest.TestCase):
    def test_pairwise_kappa_and_degenerate_prevalence(self):
        rows = [("high", "high"), ("low", "low"), ("high", "low"), ("low", "high")]
        result = pairwise_agreement(rows)
        self.assertEqual(result["exact_agreement"], 0.5)
        self.assertEqual(result["cohens_kappa"], 0.0)
        constant = pairwise_agreement([("high", "high"), ("high", "high")])
        self.assertIsNone(constant["cohens_kappa"])
        self.assertEqual(constant["exact_agreement"], 1.0)

    def test_audit_sample_stratifies_unusual_categories_without_duplicates(self):
        rows = [dict(cricsheet_match_id=str(i), match_date=f"{2015 + i % 10}-06-01",
                     source_url=f"https://provider{i % 3}.org/p", source_title="Preview",
                     overall_expected_environment=("batting_favorable", "balanced",
                         "pace_seam_favorable", "spin_slow_favorable", "uncertain")[i % 5],
                     confidence=40 if i % 4 == 0 else 80,
                     broad_eligible=i % 5 != 4) for i in range(50)]
        selected = audit_sample(rows, size=15)
        self.assertEqual(len(selected), 15)
        self.assertEqual(len({row["cricsheet_match_id"] for row in selected}), 15)
        self.assertEqual({row["overall_expected_environment"] for row in selected},
                         {"batting_favorable", "balanced", "pace_seam_favorable",
                          "spin_slow_favorable", "uncertain"})
        self.assertTrue(any(row["confidence"] < 60 for row in selected))
        self.assertTrue(any(row["confidence"] >= 75 for row in selected))

    def test_cross_model_metric_separates_c_vs_luna_from_majority_and_unanimity(self):
        assessments = [
            {"A": "pace", "B": "pace", "C": "spin"},
            {"A": "pace", "B": "spin", "C": "pace"},
            {"A": "pace", "B": "spin", "C": "spin"},
            {"A": "pace", "B": "pace", "C": "pace"},
        ]
        summary = cross_model_consensus_summary(assessments)
        self.assertEqual(summary["cross_model_consensus"]["count"], 3)
        self.assertEqual(summary["cross_model_consensus"]["proportion"], 0.75)
        self.assertEqual(summary["ordinary_majority"]["count"], 4)
        self.assertEqual(summary["three_of_three"]["count"], 1)

    def test_audit_sample_preserves_archived_and_live_routes(self):
        rows = [dict(cricsheet_match_id=str(i), match_date=f"2023-01-{i + 1:02d}",
                     source_url=f"https://provider{i % 3}.org/p",
                     source_access_route="archived_original" if i < 6 else "live_original",
                     overall_expected_environment=("uncertain", "balanced")[i % 2],
                     confidence=80, broad_eligible=i % 2 == 1) for i in range(12)]
        selected = audit_sample(rows, size=8)
        routes = [row["source_access_route"] for row in selected]
        self.assertGreaterEqual(routes.count("archived_original"), 3)
        self.assertGreaterEqual(routes.count("live_original"), 3)


if __name__ == "__main__":
    unittest.main()
