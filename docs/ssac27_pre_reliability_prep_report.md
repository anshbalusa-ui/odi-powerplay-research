## Historical evidence boundary — superseded by corrected release

This report and its output claims predate the corrected amended-source tradeoff release. In particular, the 1,094-match cohort, +0.082/−0.126 contrasts, and 0.740/0.708/0.710 validation AUCs below are historical and must never be used as current submission claims. Current release is 942 matches/1,884 paired innings, with three supported finite exchange-rate roots, corrected validation metrics, and pitch excluded. See `docs/ssac27_submission_source_of_truth.md` and unchanged `docs/ssac27_numeric_handoff.md`. The September 10 archive is unavailable and unreproduced; no 2025+ outcomes were loaded or scored.

# SSAC27 Pre-Reliability Prep Report

## Status

Completed on branch `ssac27-pre-reliability-prep`, based on the latest `main`.
No changes were merged to `main`.

**Historical snapshot, not the current pitch-measurement gate.** On
2026-09-27 the proposed pitch construct changed to model-estimated
pre-match expected playing conditions before final pitch/outcome
interpretation. Keep this report's legacy human-reliability gates and
historical outputs unchanged as provenance. See
`docs/pitch_expectation_method.md`; no new assessor passes or consensus
are claimed by this older report.

The 2025–2026 locked outcomes remain unscored and are excluded from every new
substantive result. The local second-coder file
`data/manual/pitch_reports_double_coded.csv` was not modified.

## Completed deliverables

1. **Baseline and reproducibility.** The fixed Cricsheet snapshot reproduced 3,182
   extracted matches, 2,742 core-clean matches, and 1,094 primary matches (2,188
   innings). The raw archive SHA-256 is
   `28350ee04a2ee710f959de939eb2240f737e684a2f7f93e00f3c2be26e4f415e`. Extraction
   audit: 1,120 field comparisons, zero discrepancies. Powerplay metric audit:
   zero issues.
2. **Reliability hardening.** `pitch_intercoder_reliability` now reports codable,
   unavailable, and excluded rows; per-field agreement; nominal/binary and linear
   weighted Cohen's kappa; shared-unstated and one-unstated counts; and row-level
   disagreement totals. `scripts/audit_pitch_reliability.py` writes JSON plus a
   machine-readable disagreement CSV. No reliability result was manufactured
   while the second-coder file is blank.
3. **Reconciliation workflow.** `scripts/reconcile_pitch_reliability.py` joins
   independent coders by stable match ID, preserves both raw judgments, creates
   separate `reconciled_*` fields, requires provenance for completed disagreements,
   and writes a separate final release. Synthetic tests confirm raw coder values
   remain unchanged.
4. **Independent non-pitch audit.** `scripts/audit_full_cohort_analysis.py`
   independently verified pair structure, cohort identity, approved powerplay
   definitions, and the non-pitch feature allowlist. Unlocked audit: 942 matches,
   1,884 innings, zero issues; forbidden predictors used: none.
5. **Canonical model outputs.** `artifacts/tables/ssac_full_cohort_results.json`
   and `ssac_full_cohort_model_summary.csv` contain the validation predictions,
   point metrics, clustered intervals, cohort descriptives, input hashes, and
   `locked_test_scored: false`.
6. **Actionable powerplay output.** The fixed runs+wickets model standardized
   predictions over the unlocked cohort. The empirical interquartile contrast
   from 38 to 57 runs at two wickets was `+0.082`; the contrast from one to two
   wickets at 47 runs was `-0.126`. These are model-standardized observational
   associations, not causal effects or coaching rules.
7. **Pitch interaction plan.** `scripts/run_pitch_interaction_analysis.py` records
   the fixed prespecified model specifications but refuses execution until the
   independent double-coding target and completed reconciliation worksheet pass.
   The current plan is intentionally blocked.
8. **Pitch sparsity.** `scripts/diagnose_pitch_sparsity.py` reports exact category
   and interaction-cell counts without silently collapsing sparse categories. The
   unlocked pitch subset has 178 matches; 150 cells are below the reporting
   threshold of 10 matches. No outcome fields are read by this diagnostic.
9. **Figures.** `scripts/make_ssac_figures.py` renders 300-dpi PNG and PDF
   validation model-comparison and powerplay-marginal figures plus an outcome-free
   pitch interaction coverage template. `artifacts/figures/ssac_figure_manifest.json`
   records hashes. The pitch figure is explicitly a template, not a result.
10. **Public repository audit.** `scripts/audit_public_repo.py` found no tracked
    derived datasets, local working files, or credential-like tokens; required
    public files are present. Status is `pass_with_warnings` because tracked pitch
    provenance still requires a separate source-license/terms review before public
    release.
11. **CI audit.** `scripts/audit_ci_clean_run.py` recorded a passing run of the
    exact workflow commands: 84 unit tests passed and `compileall` passed. `git
    diff --check` also passed.
12. **Abstract support.** `artifacts/abstract/ssac27_evidence.json` and its CSV
    ledger tie every permitted numeric claim to canonical outputs. The evidence
    artifact includes the 499-word limit, four required headings, two-table/figure
    limit, observational guardrail, and blocked pitch status.
13. **Abstract validator.** `src/odi_powerplay/abstract_validation.py` and
    `scripts/validate_ssac_abstract.py` enforce title/headings, word limit,
    evidence-backed numeric results, placeholder rejection, noncausal language,
    locked-outcome safeguards, figure/table count, and pitch-gate language. Tests
    cover valid, causal, structural, numeric, and premature-pitch-result failures.
14. **Abstract skeleton.** `docs/ssac27_abstract_skeleton.md` is 236 words including
    title and passes the validator. It reports only unlocked full-cohort results
    and states that pitch claims remain blocked.

## Methodology-change audit

No new research variable, feature, estimator, or hyperparameter was introduced.
The only model-code correction is `keep_empty_features=True` for the existing
numeric imputer, which preserves the fixed feature schema when a rolling fold has
an all-missing numeric column and removes the corresponding sklearn warning.
All new result scripts reuse the existing model specifications and forbidden
predictor allowlist. The pitch execution gate additionally requires a
hash-verified model table built from a separate reconciliation release and writes
pitch-specific prediction/metric paths so a future pitch run cannot overwrite the
canonical non-pitch outputs.

## Canonical unlocked results

- Primary unlocked scope: 942 matches / 1,884 team-innings from 2015–2024.
- 2024 temporal validation: 71 matches / 142 innings.
- Runs+wickets benchmark: ROC-AUC 0.740 (95% match-clustered interval
  0.642–0.822).
- Context plus powerplay model: ROC-AUC 0.708 (0.597–0.809).
- Prespecified interaction model: ROC-AUC 0.710 (0.597–0.809).
- Full model-table SHA-256:
  `ea84ac198fde324c9e388d15ef57f253e055dc83de9307f53db5404d25e8e1b9`.

## Reliability and pitch gate

The compliant reference release contains 229 matches and the deterministic blinded
sample contains 46 matches, meeting the prespecified 20% double-coding target once
an independent coder returns valid rows. The current second-coder file is blank;
therefore no kappa, agreement, reconciliation, or pitch interaction estimate is
reported. Do not execute the gated pitch pipeline until:

1. the independent file validates;
2. the reliability summary confirms the target;
3. every disagreement has a completed reconciliation value and provenance; and
4. sparsity is reviewed against the prespecified reporting output.

## Exact commands after second-coder data arrives

Run these from the repository root after independently coded rows are placed in
`data/manual/pitch_reports_double_coded.csv`:

```bash
.venv/bin/python scripts/audit_pitch_reliability.py \
  --reference-input data/manual/pitch_reports_verified.csv \
  --recoded-input data/manual/pitch_reports_double_coded.csv \
  --match-start-input data/manual/match_start_times_verified.csv

.venv/bin/python scripts/reconcile_pitch_reliability.py \
  --reference-input data/manual/pitch_reports_verified.csv \
  --recoded-input data/manual/pitch_reports_double_coded.csv \
  --output artifacts/tables/pitch_reconciliation_worksheet.csv
```

Review and complete every `pending` worksheet row, then run:

```bash
.venv/bin/python scripts/reconcile_pitch_reliability.py \
  --reference-input data/manual/pitch_reports_verified.csv \
  --recoded-input data/manual/pitch_reports_double_coded.csv \
  --reconciliation-input artifacts/tables/pitch_reconciliation_worksheet.csv \
  --final-output data/processed/pitch_reports_reconciled.csv

.venv/bin/python scripts/build_model_table.py \
  --pitch-input data/processed/pitch_reports_reconciled.csv \
  --match-start-input data/manual/match_start_times_verified.csv \
  --require-reconciled-pitch \
  --output data/processed/model_team_innings_reconciled.csv \
  --pitch-output data/processed/model_team_innings_pitch_reconciled.csv \
  --manifest-output data/processed/model_table_manifest_reconciled.json

.venv/bin/python scripts/run_pitch_interaction_analysis.py \
  --model-table data/processed/model_team_innings_pitch_reconciled.csv \
  --model-manifest data/processed/model_table_manifest_reconciled.json \
  --reliability-summary artifacts/tables/pitch_reliability.json \
  --reconciliation-input artifacts/tables/pitch_reconciliation_worksheet.csv \
  --execute

.venv/bin/python scripts/evaluate_models.py \
  --input artifacts/tables/pitch_final_validation_predictions.csv \
  --metrics-output artifacts/tables/pitch_final_validation_metrics.json \
  --calibration-output artifacts/tables/pitch_final_validation_calibration.csv
```

The gated pitch command writes pitch-specific outputs and does not overwrite the
canonical non-pitch validation predictions or metrics.

The preliminary pitch checkpoint produced by the existing reproduction pipeline is
not used as a final claim or in the SSAC evidence ledger.

## Known publication blocker

Tracked source-derived pitch provenance requires a final licence/terms review before
public release. This is separate from the completed code, reproducibility, and
measurement audits.

## Key paths

- Evidence: `artifacts/abstract/ssac27_evidence.json`
- Abstract validator result: `artifacts/abstract/ssac27_validation.json`
- Skeleton: `docs/ssac27_abstract_skeleton.md`
- Full-cohort results: `artifacts/tables/ssac_full_cohort_results.json`
- Marginal outputs: `artifacts/tables/powerplay_marginal_results.csv` and `.json`
- Pitch plan: `artifacts/tables/pitch_interaction_analysis_plan.json`
- Pitch sparsity: `artifacts/tables/pitch_sparsity_diagnostics.json` and
  `pitch_sparsity_cells.csv`
- CI evidence: `artifacts/tables/ci_clean_run.json`
- Public-repo audit: `artifacts/tables/public_repo_readiness.json`
