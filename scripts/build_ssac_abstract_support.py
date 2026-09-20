#!/usr/bin/env python3
"""Assemble an evidence-backed SSAC27 abstract support artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def model_row(results: dict[str, object], name: str) -> dict[str, object]:
    for row in results["validation_models"]:
        if row["model"] == name:
            return row
    raise ValueError(f"Canonical results are missing model {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-input",
        type=Path,
        default=ROOT / "artifacts/tables/ssac_full_cohort_results.json",
    )
    parser.add_argument(
        "--marginal-input",
        type=Path,
        default=ROOT / "artifacts/tables/powerplay_marginal_results.json",
    )
    parser.add_argument(
        "--audit-input",
        type=Path,
        default=ROOT / "artifacts/tables/full_cohort_analysis_audit.json",
    )
    parser.add_argument(
        "--sparsity-input",
        type=Path,
        default=ROOT / "artifacts/tables/pitch_sparsity_diagnostics.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/abstract/ssac27_evidence.json",
    )
    parser.add_argument(
        "--ledger-output",
        type=Path,
        default=ROOT / "artifacts/abstract/ssac27_evidence_ledger.csv",
    )
    args = parser.parse_args()

    results = read_json(args.results_input)
    marginal = read_json(args.marginal_input)
    audit = read_json(args.audit_input)
    sparsity = read_json(args.sparsity_input)
    if results.get("locked_test_scored") is not False:
        raise ValueError("Abstract support cannot use results with locked-test scoring enabled")
    if audit.get("issue_count") != 0:
        raise ValueError("Full-cohort audit has unresolved issues")

    total = results["cohort_descriptives"]["unlocked_primary_total"]
    validation = results["cohort_descriptives"]["validation"]
    benchmark = model_row(results, "powerplay_benchmark")
    m1 = model_row(results, "m1_context_powerplay")
    m2 = model_row(results, "m2_prespecified_interactions")
    contrasts = marginal["contrasts"]
    pitch_matches = sparsity["matches_by_split"]
    unlocked_pitch_matches = int(pitch_matches.get("development", 0)) + int(
        pitch_matches.get("validation", 0)
    )

    ledger = [
        {
            "claim_id": "cohort",
            "status": "allowed",
            "claim": (
                f"The unlocked primary cohort contains {total['matches']} matches and "
                f"{total['rows']} team-innings from 2015 through 2024."
            ),
            "source_artifact": str(args.results_input),
            "source_selector": "cohort_descriptives.unlocked_primary_total",
        },
        {
            "claim_id": "validation",
            "status": "allowed",
            "claim": (
                f"Temporal validation covers {validation['matches']} matches and "
                f"{validation['rows']} innings from 2024."
            ),
            "source_artifact": str(args.results_input),
            "source_selector": "cohort_descriptives.validation",
        },
        {
            "claim_id": "model",
            "status": "allowed_associational",
            "claim": (
                f"The fixed runs+wickets benchmark had validation ROC-AUC "
                f"{benchmark['roc_auc']:.3f} (95% interval "
                f"{benchmark['roc_auc_lower_95']:.3f}–{benchmark['roc_auc_upper_95']:.3f})."
            ),
            "source_artifact": str(args.results_input),
            "source_selector": "validation_models[model=powerplay_benchmark]",
        },
        {
            "claim_id": "adjusted_model",
            "status": "allowed_associational",
            "claim": (
                f"Adding pre-match context to powerplay runs and wickets yielded validation "
                f"ROC-AUC {m1['roc_auc']:.3f}; the pre-specified interaction model yielded "
                f"{m2['roc_auc']:.3f}."
            ),
            "source_artifact": str(args.results_input),
            "source_selector": "validation_models[m1_context_powerplay,m2_prespecified_interactions]",
        },
        {
            "claim_id": "actionable",
            "status": "allowed_associational",
            "claim": (
                "Model-standardized predicted probability changed by "
                f"{contrasts['runs_low_to_high_at_middle_wickets']['difference']:+.3f} across "
                "the empirical interquartile run contrast at middle wickets, and by "
                f"{contrasts['wickets_low_to_high_at_middle_runs']['difference']:+.3f} across "
                "the empirical interquartile wicket contrast at middle runs."
            ),
            "source_artifact": str(args.marginal_input),
            "source_selector": "contrasts",
        },
        {
            "claim_id": "pitch_status",
            "status": "blocked",
            "claim": (
                f"Pitch interaction results are blocked: the outcome-blind pitch subset has "
                f"{unlocked_pitch_matches} unlocked matches, but independent reliability and "
                "reconciliation are not cleared."
            ),
            "source_artifact": str(args.sparsity_input),
            "source_selector": "matches_by_split",
        },
    ]

    support = {
        "artifact_version": 1,
        "title": "What Makes a Successful ODI Powerplay?",
        "abstract_requirements": {
            "headings": ["Introduction", "Methods", "Results", "Conclusion"],
            "word_limit_including_title": 499,
            "maximum_tables_and_figures_combined": 2,
            "requires_actual_results": True,
        },
        "analysis_scope": results["analysis_scope"],
        "locked_test_scored": False,
        "locked_test_outcomes_loaded": False,
        "interpretation": "All substantive estimates are observational associations.",
        "cohort": total,
        "validation": validation,
        "models": {
            "powerplay_benchmark": benchmark,
            "m1_context_powerplay": m1,
            "m2_prespecified_interactions": m2,
        },
        "actionable_powerplay": contrasts,
        "pitch_measurement": {
            "matches_by_split": pitch_matches,
            "unlocked_matches": unlocked_pitch_matches,
            "sparse_cell_count": sparsity["sparse_cell_count"],
            "reliability_status": "not_cleared",
            "reconciliation_status": "not_cleared",
            "pitch_interaction_claim_allowed": False,
        },
        "evidence_ledger": ledger,
        "source_artifacts": {
            str(path): sha256(path)
            for path in (args.results_input, args.marginal_input, args.audit_input, args.sparsity_input)
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(support, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.ledger_output.parent.mkdir(parents=True, exist_ok=True)
    with args.ledger_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(ledger[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ledger)
    print(json.dumps(support, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
