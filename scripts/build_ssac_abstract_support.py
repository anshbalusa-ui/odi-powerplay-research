#!/usr/bin/env python3
"""Build current SSAC27 abstract evidence only from the verified corrected release."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RELEASE = (
    "analysis_manifest.json", "statistical_qa.json", "context_exchange_rates.json",
    "paired_context_differences.json", "primary_model_metrics.json", "validation_metrics.json",
    "sensitivity_summary.json",
)
TITLE = "What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def close(a: float, b: float, tol: float = .00051) -> bool:
    return abs(float(a) - b) <= tol


def verify_release(directory: Path, handoff: Path) -> dict[str, Any]:
    """Fail closed unless manifests, QA, handoff and core corrected results reconcile."""
    directory, handoff = directory.resolve(), handoff.resolve()
    manifest_path = directory / "release_manifest.json"
    manifest = load(manifest_path)
    if manifest.get("status") != "amended_source_unlocked_2015_2024_only":
        raise ValueError("release status is not the corrected amended-source release")
    if manifest.get("original_fixed_september_10_archive_reproduced") is not False:
        raise ValueError("release archive identity gate failed")
    if (manifest.get("archive_sha256") != "f8423531b24183bc2cfc1e3e27f9bd29ad7c4d5a4bdc2469bf681d7fe2f5c5ce"
            or manifest.get("input_table_sha256") != "8a6330c7974219f690a85188fefdec75562427fb25cb4dab2c1b3784a91aa958"):
        raise ValueError("corrected archive or input-table identity mismatch")
    hashes = manifest.get("release_files_sha256", {})
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("release manifest is malformed or contains no artifact hashes")
    for name, expected in hashes.items():
        path = directory / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"release SHA-256 mismatch or missing file: {name}")
    for name in REQUIRED_RELEASE:
        if name not in hashes:
            raise ValueError(f"release manifest omits required artifact: {name}")
    qa = load(directory / "statistical_qa.json")
    if qa.get("pass") is not True:
        raise ValueError("statistical QA did not pass")
    raw = qa.get("raw_manifest", {})
    if (qa.get("locked_rows_read") != 0 or qa.get("locked_data_audit_scored") is not False
            or qa.get("locked_data_audit_outcomes_loaded") is not False
            or raw.get("archive_sha256_verified") is not True
            or raw.get("registry_sha256_verified") is not True
            or raw.get("locked_registry_match_count_metadata_only") != 152):
        raise ValueError("locked-period or archive identity gate failed")
    analysis = load(directory / "analysis_manifest.json")
    if (analysis.get("locked_rows_read") != 0 or analysis.get("input_rows") != 1884
            or analysis.get("development_matches") != 871 or analysis.get("development_rows") != 1742
            or analysis.get("validation_matches") != 71 or analysis.get("validation_rows") != 142):
        raise ValueError("analysis manifest cohort or lock identity mismatch")
    if (analysis.get("source_sha256") != manifest.get("input_table_sha256")
            or qa.get("analysis_manifest_source_sha256_matches_input") is not True
            or raw.get("archive_sha256") != manifest.get("archive_sha256")):
        raise ValueError("source table or archive identity mismatch")
    if not handoff.is_file():
        raise ValueError("canonical numeric handoff is missing")
    if sha256(handoff) != "9c4fffc1bfb1c75734c9546f2a47ab4de9a9de7de74811a2e3ce64160ec4c909":
        raise ValueError("canonical handoff SHA-256 mismatch")
    if sha256(manifest_path) != "99574bd3b67b20ee68face49ad58e155c08811b5f6229a9e7b2084b3effdcdcf":
        raise ValueError("corrected release manifest SHA-256 mismatch")
    handoff_text = handoff.read_text(encoding="utf-8")
    for fact in ("942 clean 2015–2024 men's ODI matches", "1,884 paired team innings", "3 of 18", "14.143", "13.248", "29.763", "0.6626", "0.6737", "0.6784", "not** causal"):
        if fact.casefold() not in handoff_text.casefold():
            raise ValueError(f"canonical handoff is missing required corrected fact: {fact}")
    primary = load(directory / "primary_model_metrics.json")
    exchange = load(directory / "context_exchange_rates.json")
    paired = load(directory / "paired_context_differences.json")
    validation = load(directory / "validation_metrics.json")
    if primary.get("amended_source_only") is not True or primary.get("locked_rows_read") != 0:
        raise ValueError("primary model provenance gate failed")
    if primary.get("primary_root_contexts") != 18 or len(exchange) != 54 or sum(r.get("contrast") == "primary_1_to_2" for r in exchange) != 18:
        raise ValueError("primary context grid is inconsistent")
    roots = [r for r in exchange if r.get("contrast") == "primary_1_to_2" and r.get("defined") is True]
    if len(roots) != 3 or len(primary.get("primary_defined_roots", [])) != 3:
        raise ValueError("primary supported-root count is inconsistent")
    expected = (
        (13.248, 4.713, 17.481, 758),
        (14.143, 4.124, 18.450, 735),
        (29.763, 13.844, 30.934, 563),
    )
    ordered_roots = sorted(roots, key=lambda r: r["runs_per_wicket"])
    for (value, lower, upper, valid), row in zip(expected, ordered_roots):
        if not close(row["runs_per_wicket"], value):
            raise ValueError("primary root estimates disagree with corrected handoff")
        ci = row.get("bootstrap_ci", {}).get("runs_per_wicket")
        if (not ci or ci.get("valid_replicates") != valid
                or not close(ci.get("lower_95", float("nan")), lower)
                or not close(ci.get("upper_95", float("nan")), upper)):
            raise ValueError("primary root bootstrap counts or interval mismatch")
    if qa.get("primary_root_bootstrap_valid_counts") != [735, 758, 563]:
        raise ValueError("QA primary root bootstrap counts mismatch")
    if any(r.get("support_start", {}).get("supported") is not True or r.get("support_target", {}).get("supported") is not True for r in exchange if r.get("contrast") == "primary_1_to_2"):
        raise ValueError("primary context support gate failed")
    counts = primary.get("development_refit_bootstrap", {})
    if counts.get("requested") != 1000 or counts.get("valid") != 1000 or counts.get("failed") != 0:
        raise ValueError("development refit counts mismatch")
    if len(paired) != 90 or primary.get("paired_context_comparisons") != 90 or qa.get("paired_context_rows") != 90:
        raise ValueError("paired status rows mismatch")
    root_comparisons = [r for r in paired if r.get("quantity") == "runs_per_wicket"]
    if len(root_comparisons) != 45 or sum(r.get("estimate") is not None for r in root_comparisons) != 2:
        raise ValueError("paired root point-estimate status mismatch")
    for row in root_comparisons:
        valid = row.get("valid_paired_replicates", 0)
        requested = row.get("requested_replicates", 1000)
        if row.get("lower_95") is not None and valid < .8 * requested:
            raise ValueError("paired root interval violates frozen 80% validity threshold")
    if any(r.get("lower_95") is not None or r.get("upper_95") is not None for r in root_comparisons if r.get("estimate") is None):
        raise ValueError("paired root interval exists where a point difference is undefined")
    for name, auc, loss in (("six_term_primary", .6626, .6726), ("additive_benchmark", .6737, .6650), ("four_term_interaction", .6784, .6669)):
        model = validation.get(name, {})
        metrics = model.get("metrics", {})
        if model.get("status") != "fit" or model.get("n_matches") != 71 or model.get("n_rows") != 142:
            raise ValueError(f"validation count mismatch: {name}")
        boot = model.get("validation_bootstrap", {})
        if boot.get("requested") != 2000 or boot.get("valid") != 2000 or not close(metrics.get("roc_auc", 0), auc) or not close(metrics.get("log_loss", 0), loss):
            raise ValueError(f"validation metric mismatch: {name}")
    neutral = {}
    for innings, name in ((1, "batting_first"), (0, "chase")):
        row = next((r for r in exchange if r.get("contrast") == "primary_1_to_2" and r.get("innings") == innings and r.get("elo_state") == 2 and r.get("venue_state") == 2), None)
        if row is None:
            raise ValueError("neutral fixed-run context is missing")
        boot = row.get("bootstrap_ci", {}).get("fixed_run_probability_difference", {})
        if not boot or boot.get("valid_replicates") != 1000:
            raise ValueError("neutral fixed-run bootstrap interval is missing")
        neutral[name] = {"probability_from": row["probability_fixed_run_from"], "probability_to": row["probability_fixed_run_to"], "difference": row["probability_difference_fixed_run"], "ci_lower": boot["lower_95"], "ci_upper": boot["upper_95"], "valid_refits": boot["valid_replicates"]}
    paired_neutral = next((r for r in paired if r.get("axis") == "innings" and r.get("quantity") == "fixed_run_probability_difference" and r.get("context_a") == {"innings": 1, "elo_state": 2, "venue_state": 2} and r.get("context_b") == {"innings": 0, "elo_state": 2, "venue_state": 2}), None)
    if (not paired_neutral or paired_neutral.get("valid_paired_replicates") != 1000
            or not close(paired_neutral.get("estimate", 0) * 100, 5.185)
            or not close(paired_neutral.get("lower_95", 0) * 100, -.457)
            or not close(paired_neutral.get("upper_95", 0) * 100, 11.182)):
        raise ValueError("neutral paired probability contrast does not match corrected release")
    if (not close(neutral["batting_first"]["probability_from"], .5046)
            or not close(neutral["batting_first"]["probability_to"], .3995)
            or not close(neutral["chase"]["probability_from"], .5578)
            or not close(neutral["chase"]["probability_to"], .4009)):
        raise ValueError("neutral fixed-run estimates do not match corrected handoff")
    if qa.get("primary_context_cell_count") != 18 or qa.get("primary_finite_root_count") != 3 or qa.get("development_matches") != 871 or qa.get("validation_matches") != 71 or qa.get("validation_bootstrap_counts_reconcile") is not True:
        raise ValueError("statistical QA release reconciliations failed")
    return {"manifest": manifest, "analysis": analysis, "qa": qa, "primary": primary, "exchange": exchange, "paired": paired, "validation": validation, "neutral": neutral, "paired_neutral": paired_neutral}


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def build_support(release_dir: Path, handoff: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    d = verify_release(release_dir, handoff)
    analysis, primary, validation = d["analysis"], d["primary"], d["validation"]
    roots = sorted(primary["primary_defined_roots"], key=lambda r: r["runs_per_wicket"])
    models = {k: validation[k] for k in ("six_term_primary", "additive_benchmark", "four_term_interaction")}
    cohort = {"matches": 942, "rows": 1884, "development": {"matches": 871, "rows": 1742}, "validation": {"matches": 71, "rows": 142}}
    contexts = {"starting_runs": 47, "wickets_from": 1, "wickets_to": 2, "contexts_total": 18, "defined_roots": 3,
                "undefined_roots": 15, "roots": [{"runs_per_wicket": round(r["runs_per_wicket"], 3), "ci_lower": round(r["bootstrap_ci"]["runs_per_wicket"]["lower_95"], 3), "ci_upper": round(r["bootstrap_ci"]["runs_per_wicket"]["upper_95"], 3), "valid_refits": r["bootstrap_ci"]["runs_per_wicket"]["valid_replicates"]} for r in roots]}
    source_names = (*REQUIRED_RELEASE, "release_manifest.json")
    source_artifacts = {repo_path(release_dir / n): sha256(release_dir / n) for n in source_names}
    source_artifacts[repo_path(handoff)] = sha256(handoff)
    ledger = [
        {"claim_id": "cohort", "status": "allowed", "claim": "942 clean men's ODIs / 1,884 paired innings (871 development; 71 untouched 2024 validation).", "source_artifact": "artifacts/ssac27_tradeoff/analysis_manifest.json", "source_selector": "cohort and split counts"},
        {"claim_id": "exchange_rate", "status": "allowed_associational", "claim": "At 47 runs and 1→2 wickets, 3 of 18 contexts have finite roots: 14.143 (4.124–18.450; 735/1,000), 13.248 (4.713–17.481; 758/1,000), and 29.763 (13.844–30.934; 563/1,000); 15 are undefined, not zero.", "source_artifact": "artifacts/ssac27_tradeoff/primary_model_metrics.json", "source_selector": "primary_defined_roots"},
        {"claim_id": "validation", "status": "allowed_associational", "claim": "2024 six-term primary ROC-AUC 0.6626, log loss 0.6726; additive 0.6737 / 0.6650; four-term 0.6784 / 0.6669. The primary did not improve AUC or log loss.", "source_artifact": "artifacts/ssac27_tradeoff/validation_metrics.json", "source_selector": "three frozen model metrics"},
        {"claim_id": "paired_context", "status": "allowed_with_caveat", "claim": "45 paired comparisons / 90 status rows; only two point root differences, neither with a valid paired CI under the 80% joint-refit rule.", "source_artifact": "artifacts/ssac27_tradeoff/paired_context_differences.json", "source_selector": "paired root-difference statuses"},
        {"claim_id": "neutral_fixed_run", "status": "allowed_associational", "claim": "At neutral Elo and median earlier-date venue scoring, 47 runs and 1→2 wickets: batting first 0.5046→0.3995 (−10.505 points; interval −15.473 to −7.215), chase 0.5578→0.4009 (−15.690; −20.614 to −12.698).", "source_artifact": "artifacts/ssac27_tradeoff/context_exchange_rates.json", "source_selector": "primary_1_to_2; elo_state=2; venue_state=2; innings=1,0"},
        {"claim_id": "neutral_paired", "status": "allowed_with_caveat", "claim": "Neutral first-minus-chase wicket-loss probability contrast +5.185 percentage points (paired interval −0.457 to +11.182); interval includes zero, so no established innings-order difference.", "source_artifact": "artifacts/ssac27_tradeoff/paired_context_differences.json", "source_selector": "innings; fixed_run_probability_difference; elo_state=2; venue_state=2"},
        {"claim_id": "bootstrap_qa", "status": "allowed", "claim": "Independent statistical QA passed; 1,000/1,000 development match refits and 2,000/2,000 validation match resamples per model, with no 2025+ outcome records read.", "source_artifact": "artifacts/ssac27_tradeoff/statistical_qa.json", "source_selector": "pass; development_bootstrap; validation_bootstrap_counts_reconcile; locked_rows_read"},
        {"claim_id": "locked_period", "status": "allowed_with_caveat", "claim": "152 2025+ registry IDs were counted from metadata only; no such match records or outcomes opened, fit or scored.", "source_artifact": "artifacts/ssac27_tradeoff/statistical_qa.json", "source_selector": "raw_manifest.locked_registry_match_count_metadata_only; locked_rows_read"},
        {"claim_id": "locked_outcome_result", "status": "blocked", "claim": "Any 2025+ match-outcome result or locked-test score is prohibited.", "source_artifact": "artifacts/ssac27_tradeoff/statistical_qa.json", "source_selector": "locked_data_audit_scored; locked_rows_read"},
        {"claim_id": "pitch", "status": "blocked", "claim": "Pitch–outcome results are blocked: pitch is excluded; model-estimated pre-match expected playing environment is unapproved for outcome analysis.", "source_artifact": "docs/ssac27_numeric_handoff.md", "source_selector": "claim boundary"},
        {"claim_id": "historical_pitch", "status": "historical_only", "claim": "Historical source-stated pre-match pitch effects are a separate re-audited derivative, not this model's pitch interaction.", "source_artifact": "docs/ssac27_numeric_handoff.md", "source_selector": "claim boundary"},
    ]
    support = {"artifact_version": 2, "title": TITLE, "analysis_scope": "amended_source_unlocked_2015_2024_only", "locked_test_scored": False, "locked_test_outcomes_loaded": False,
        "cohort": cohort, "primary_estimand": contexts, "validation_models": {name: {"roc_auc": round(v["metrics"]["roc_auc"], 4), "log_loss": round(v["metrics"]["log_loss"], 4), "brier_score": round(v["metrics"]["brier_score"], 4), "accuracy": round(v["metrics"]["accuracy_at_0_5"], 4), "roc_auc_ci": [round(v["validation_bootstrap"]["metrics"]["roc_auc"]["lower_95"], 4), round(v["validation_bootstrap"]["metrics"]["roc_auc"]["upper_95"], 4)]} for name,v in models.items()},
        "pitch_measurement": {"pitch_interaction_claim_allowed": False, "model_estimated_expected_environment_outcome_analysis_approved": False}, "source_artifacts": source_artifacts, "evidence_ledger": ledger,
        "neutral_fixed_run_contrasts": d["neutral"], "neutral_paired_context_difference": {"estimate": d["paired_neutral"]["estimate"], "lower_95": d["paired_neutral"]["lower_95"], "upper_95": d["paired_neutral"]["upper_95"], "valid_paired_replicates": d["paired_neutral"]["valid_paired_replicates"]}}
    support["release_manifest_sha256"] = sha256(release_dir / "release_manifest.json")
    support["canonical_handoff"] = repo_path(handoff)
    return support, ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, default=ROOT / "artifacts/ssac27_tradeoff")
    parser.add_argument("--handoff", type=Path, default=ROOT / "docs/ssac27_numeric_handoff.md")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/abstract/ssac27_evidence.json")
    parser.add_argument("--ledger-output", type=Path, default=ROOT / "artifacts/abstract/ssac27_evidence_ledger.csv")
    args = parser.parse_args()
    support, ledger = build_support(args.release_dir, args.handoff)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(support, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.ledger_output.parent.mkdir(parents=True, exist_ok=True)
    with args.ledger_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)
    print(json.dumps(support, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
