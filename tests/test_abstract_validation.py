from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from odi_powerplay.abstract_validation import validate_ssac_abstract  # noqa: E402


class AbstractValidationTests(unittest.TestCase):
    def evidence(self) -> dict[str, object]:
        model = {"roc_auc": 0.740}
        return {
            "locked_test_scored": False,
            "cohort": {"matches": 942, "rows": 1884},
            "validation": {"matches": 71, "rows": 142},
            "models": {
                "powerplay_benchmark": model,
                "m1_context_powerplay": {"roc_auc": 0.708},
                "m2_prespecified_interactions": {"roc_auc": 0.710},
            },
            "pitch_measurement": {"pitch_interaction_claim_allowed": False},
        }

    def test_accepts_evidence_backed_observational_draft(self) -> None:
        text = """# What Makes a Successful ODI Powerplay?

## Introduction
We studied which first-10-over batting profiles were associated with winning in men's ODIs.

## Methods
We analyzed 942 matches (1884 team-innings) from 2015–2024 and held out 71 matches (142 innings) for temporal validation. Models were fit without locked-period outcomes. Pitch interaction analyses were not reported pending independent reliability and reconciliation. All estimates are observational and not causal.

## Results
The fixed runs-and-wickets benchmark had validation ROC-AUC 0.740; adding context yielded 0.708, and the pre-specified interaction model yielded 0.710.

## Conclusion
Powerplay runs and wicket preservation were associated with subsequent match winning probability. These results support transparent, noncausal decision framing rather than a deterministic coaching rule.
"""

        result = validate_ssac_abstract(text, self.evidence())

        self.assertTrue(result["valid"], result["issues"])
        self.assertLessEqual(result["word_count_including_title"], 499)
        self.assertEqual(result["canonical_evidence_values_present"], 7)

    def test_rejects_missing_structure_causal_language_and_numbers(self) -> None:
        text = """# Draft
## Methods
Powerplay runs cause winning.
"""

        result = validate_ssac_abstract(text, self.evidence())

        codes = {issue["code"] for issue in result["issues"]}
        self.assertFalse(result["valid"])
        self.assertIn("heading", codes)
        self.assertIn("causal_language", codes)
        self.assertIn("evidence_numbers", codes)

    def test_rejects_unapproved_pitch_result_sentence(self) -> None:
        text = """# Title
## Introduction
We study associated outcomes.
## Methods
We use 942 matches and 1884 innings.
## Results
Pitch effects improved winning probability; validation included 71 matches and 142 innings with ROC-AUC 0.740, 0.708, and 0.710.
## Conclusion
The result is observational and not causal.
"""

        result = validate_ssac_abstract(text, self.evidence())

        self.assertIn("pitch_gate", {issue["code"] for issue in result["issues"]})


if __name__ == "__main__":
    unittest.main()
