"""Model agreement is a stability diagnostic, not pitch truth."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from odi_powerplay.pitch_expectation import pairwise_agreement, audit_sample  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
