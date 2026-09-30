from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odi_powerplay.abstract_validation import validate_ssac_abstract  # noqa: E402


class AbstractValidationTests(unittest.TestCase):
    def evidence(self) -> dict[str, object]:
        return {
            "artifact_version": 2,
            "analysis_scope": "amended_source_unlocked_2015_2024_only",
            "locked_test_scored": False,
            "locked_test_outcomes_loaded": False,
            "cohort": {"matches": 942, "rows": 1884, "development": {"matches": 871, "rows": 1742}, "validation": {"matches": 71, "rows": 142}},
            "primary_estimand": {"starting_runs": 47, "wickets_from": 1, "wickets_to": 2, "contexts_total": 18, "defined_roots": 3, "undefined_roots": 15, "roots": [{"runs_per_wicket": 13.248, "ci_lower": 4.713, "ci_upper": 17.481, "valid_refits": 758}, {"runs_per_wicket": 14.143, "ci_lower": 4.124, "ci_upper": 18.450, "valid_refits": 735}, {"runs_per_wicket": 29.763, "ci_lower": 13.844, "ci_upper": 30.934, "valid_refits": 563}]},
            "validation_models": {"six_term_primary": {"roc_auc": .6626, "log_loss": .6726}, "additive_benchmark": {"roc_auc": .6737, "log_loss": .6650}, "four_term_interaction": {"roc_auc": .6784, "log_loss": .6669}},
            "pitch_measurement": {"pitch_interaction_claim_allowed": False},
            "source_artifacts": {"artifacts/ssac27_tradeoff/release_manifest.json": "99574bd3b67b20ee68face49ad58e155c08811b5f6229a9e7b2084b3effdcdcf", "docs/ssac27_numeric_handoff.md": "9c4fffc1bfb1c75734c9546f2a47ab4de9a9de7de74811a2e3ce64160ec4c909"},
            "release_manifest_sha256": "99574bd3b67b20ee68face49ad58e155c08811b5f6229a9e7b2084b3effdcdcf",
            "canonical_handoff": "docs/ssac27_numeric_handoff.md",
            "evidence_ledger": [{"claim_id": "pitch", "status": "blocked"}, {"claim_id": "prior", "status": "historical_only"}],
            "neutral_fixed_run_contrasts": {"batting_first": {"probability_from": .5046, "probability_to": .3995, "difference": -.10505, "ci_lower": -.15473, "ci_upper": -.07215, "valid_refits": 1000}, "chase": {"probability_from": .5578, "probability_to": .4009, "difference": -.15690, "ci_lower": -.20614, "ci_upper": -.12698, "valid_refits": 1000}},
            "neutral_paired_context_difference": {"estimate": .05185, "lower_95": -.00457, "upper_95": .11182, "valid_paired_replicates": 1000},
        }

    def draft(self) -> str:
        return """# What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket

## Introduction
We estimate observational run-wicket tradeoffs associated with ODI match-win probability.

## Methods
The amended-source analysis included 942 men's ODI matches and 1884 paired innings: 871 matches (1742 innings) for development and 71 (142 innings) for untouched 2024 validation. At 47 first-ten-over runs, we estimate the bounded nonnegative exchange rate for losing a wicket from 1 to 2 across 18 contexts. The model is associational, not causal. Pitch is excluded. 2025+ outcomes were metadata-only and not opened or scored.

## Results
Only 3 of 18 contexts had finite roots: 14.143 runs (95% CI 4.124–18.450; 735/1000 refits), 13.248 (4.713–17.481; 758/1000), and 29.763 (13.844–30.934; 563/1000). The other 15 roots were undefined, not zero. At neutral strength and median venue scoring, first-innings probability changed from 0.5046 to 0.3995 (−10.505 percentage points; 95% CI −15.473 to −7.215); chase probability changed from 0.5578 to 0.4009 (−15.690 points; 95% CI −20.614 to −12.698). The first-minus-chase paired contrast was 5.185 points (95% CI −0.457 to +11.182). Validation ROC-AUC and log loss were 0.6626 (0.5461–0.7681) and 0.6726 for the primary; additive benchmark 0.6737 and 0.6650; four-term interaction 0.6784 and 0.6669. The primary did not improve AUC or log loss.

## Conclusion
The conditional associations vary by context and do not define a universal wicket price. Undefined rates are not zero; estimates are not causal effects.
"""

    def test_accepts_locked_period_nonuse_guardrail(self) -> None:
        text = self.draft().replace("2025+ outcomes were metadata-only and not opened or scored.", "Outcomes from 2025 onward were not loaded or scored.")
        result = validate_ssac_abstract(text, self.evidence())
        self.assertTrue(result["valid"], result["issues"])
    def test_accepts_current_corrected_observational_draft(self) -> None:
        result = validate_ssac_abstract(self.draft(), self.evidence())
        self.assertTrue(result["valid"], result["issues"])
        self.assertLessEqual(result["word_count_including_title"], 499)

    def test_blocks_legacy_auc_even_alongside_current_results(self) -> None:
        text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss. Earlier powerplay validation ROC-AUC was 0.740.")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("stale_result", codes)

    def test_blocks_all_superseded_result_claims_even_with_corrected_values(self) -> None:
        for obsolete in ("0.708", "0.710", "+0.082", "−0.126", "1,094 matches"):
            with self.subTest(obsolete=obsolete):
                text = self.draft().replace("The primary did not improve AUC or log loss.", f"The primary did not improve AUC or log loss. Earlier submission model: {obsolete}.")
                codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
                self.assertIn("stale_result", codes)

    def test_blocks_unsupported_paired_root_interval(self) -> None:
        text = self.draft().replace("The other 15 roots were undefined, not zero.", "The other 15 roots were undefined, not zero. The strong-Elo first-minus-chase root difference had a paired 95% CI of −25 to −4 runs.")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("unsupported_root", codes)

    def test_rejects_three_assets_mentioned_inline(self) -> None:
        text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss (Figure 1, Figure 2, Table 1).")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("figure_table_limit", codes)

    def test_accepts_two_combined_assets(self) -> None:
        text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss (Figure 1 and Table 1).")
        result = validate_ssac_abstract(text, self.evidence())
        self.assertTrue(result["valid"], result["issues"])
        self.assertEqual(result["figure_table_count"], 2)

    def test_rejects_word_limit_and_missing_sections(self) -> None:
        text = self.draft().replace("## Conclusion", "## Discussion") + " observational" * 500
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("word_limit", codes)
        self.assertIn("heading", codes)

    def test_disclaimers_do_not_cancel_positive_claims_in_same_sentence(self) -> None:
        for claim, code in (
            ("Wickets cause victories, but this is not causal.", "causal_language"),
            ("Pitch interactions improved outcomes, but pitch was excluded.", "pitch_gate"),
            ("We scored the 2025 outcomes, although 2025+ outcomes were not scored.", "locked_outcome"),
        ):
            with self.subTest(claim=claim):
                text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss. " + claim)
                codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
                self.assertIn(code, codes)

    def test_blocks_causal_synonyms_and_separately_assigned_zero_roots(self) -> None:
        for claim in (
            "Losing a wicket reduces win probability; this is not causal.",
            "Extra wickets increase winning chances.",
            "Wicket loss lowers the chance of winning.",
        ):
            with self.subTest(claim=claim):
                text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss. " + claim)
                codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
                self.assertIn("causal_language", codes)
        text = self.draft().replace("The primary did not improve AUC or log loss.", "The primary did not improve AUC or log loss. The 15 unavailable roots were assigned zero runs.")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("unsupported_root", codes)

    def test_blocks_universal_or_zero_root_claims(self) -> None:
        text = self.draft().replace("do not define a universal wicket price", "define a universal wicket price")
        text = text.replace("undefined, not zero", "undefined roots are zero")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("universal_rate", codes)
        self.assertIn("unsupported_root", codes)

    def test_blocks_pitch_findings_and_locked_result_even_with_remote_guardrails(self) -> None:
        text = self.draft().replace("Pitch is excluded.", "A pitch interaction improved winning probability.")
        text = text.replace("2025+ outcomes were metadata-only and not opened or scored.", "We scored the 2025 outcomes.")
        text += "\nThis is not causal. 2025+ data are not discussed."
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("pitch_gate", codes)
        self.assertIn("locked_outcome", codes)

    def test_requires_current_evidence_identity(self) -> None:
        bad = self.evidence()
        bad["artifact_version"] = 1
        codes = {issue["code"] for issue in validate_ssac_abstract(self.draft(), bad)["issues"]}
        self.assertIn("evidence_gate", codes)

    def test_causal_claim_is_not_cured_by_unrelated_disclaimer(self) -> None:
        text = self.draft().replace("conditional associations vary", "conditional associations cause variation")
        codes = {issue["code"] for issue in validate_ssac_abstract(text, self.evidence())["issues"]}
        self.assertIn("causal_language", codes)


if __name__ == "__main__":
    unittest.main()
