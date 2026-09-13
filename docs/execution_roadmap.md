# Execution Roadmap

## Delivery strategy

The project has two linked timelines:

1. **SSAC27 milestone:** a complete, reproducible result from the broad modern men's ODI cohort by the October 1, 2026 abstract deadline.
2. **Expanded paper:** the broader ODI study continues after submission, whether or not the abstract advances.

The SSAC deadline changes sequencing, not scientific standards. Scope may be reduced for specific source-stated pitch-effect variables if source coverage is inadequate, but the match cohort is not World-Cup-only.

## Build order

The project should be built in seven gates. Do not begin final modeling until the preceding gate passes.

### Gate 1 — Lock the protocol and scope

**Goal:** prevent outcome-driven decisions.

- Confirm the 2015-forward men's ODI primary era and fixed data-snapshot cutoff; do not filter by event.
- Freeze primary hypotheses, cohort rules, prediction timestamp, lean **source-stated pitch-effect codebook**, feature sets, and final test period.
- Freeze the rule that no pitch effect may be inferred from physical surface descriptions by the researcher.
- Choose confirmatory versus exploratory interactions.
- Create an empty results shell before examining final-test outcomes.

**Pass condition:** a dated protocol is committed and all matches from 2025 through the fixed 2026 snapshot are treated as locked test data.

### Gate 2 — Validate Cricsheet extraction

**Goal:** create a trusted match/innings foundation.

- Download official ODI JSON and record checksums.
- Run the existing extractor.
- Build a cohort-flow table.
- Randomly choose at least 20 team-innings across years and hand-check first-10-over score, wickets, legal balls, boundaries, dots, toss, innings order, and result against the source JSON/scorecard.
- Add a regression test for every discovered edge case.

**Pass condition:** all unit tests pass and the hand-audit discrepancy rate is reported and resolved.

### Gate 3 — Build the context tables

**Goal:** create only pre-match context.

- Construct a canonical venue crosswalk.
- Add cited scheduled local start times.
- Calculate pre-match Elo and rolling strength without same-day/future leakage.
- Produce unmatched/ambiguous audit reports.

**Pass condition:** every eligible match has validated IDs; no post-match strength data are used.

### Gate 4 — Collect and validate source-stated pre-match pitch effects

**Goal:** make source-derived pitch expectations transparent without independent researcher pitch analysis.

- Collect eligible pre-match pitch reports using a prespecified design spanning years, venues, teams, and competition types without inspecting outcomes.
- Standardize only the playing effects explicitly stated by each source.
- Do **not** infer spin from dry/dusty/cracked wording, pace/seam from grass/green/moist wording, batting ease from hard/flat wording, or slow/two-paced behavior from used/worn/tacky wording unless the source itself states that effect.
- Retain physical surface descriptions only in short provenance paraphrases.
- If complete report coverage is infeasible, define a source-audited analysis subset without inspecting outcomes and report its selection/coverage limits.
- Double-code a stratified random 20% and calculate reliability using the same explicit-source-only rule.
- Keep explicit dew expectation secondary.
- Inspect missingness, unsupported codes, and inconsistent values.

**Pass condition:** source coverage, inter-coder reliability, source-stated effect-field missingness, and compliance with the no-inference rule are documented.

### Gate 5 — Freeze the model table

**Goal:** prevent leakage and analytic drift.

- Merge one-to-one match tables before expanding to team-innings.
- Apply the feature allowlist.
- Prohibit raw physical surface descriptors and any researcher-inferred pitch labels from the model table.
- Create a correlation report.
- Remove deterministic/redundant pairs from the same specification.
- Save development/test IDs and hash the table.

**Pass condition:** no match crosses splits, no forbidden column enters predictors, and test IDs are locked.

### Gate 6 — Model and evaluate

**Goal:** compare simple and complex models fairly.

- Fit baseline and logistic models first.
- Tune RF/XGBoost only in chronological development folds.
- Freeze all model objects and parameters.
- Score the locked test once.
- Compute match-clustered bootstrap CIs, calibration, permutation importance, and SHAP.
- Interpret pitch interactions only as interactions with **source-stated pre-match expectations**, never as direct physical-surface measurements.

**Pass condition:** every model has the same eligible test rows, saved probabilities, required metrics, and confidence intervals.

### Gate 7 — Write and release

**Goal:** produce an honest, reproducible paper.

- Build figures from saved tables, never by manual editing.
- Write methods before interpreting results.
- Distinguish confirmatory and exploratory results.
- Describe pitch variables as standardized source statements, not researcher diagnoses of the surface.
- Discuss measurement error, selection bias, sample size, source coverage, and non-causal interpretation.
- Run the project from a clean environment and compare output hashes.

**Pass condition:** a new user can reproduce the derived analysis from documented inputs, subject to source access terms.

## Suggested 10-week schedule

| Week | Deliverable |
|---|---|
| 1 | protocol, hypotheses, scope, source/legal check |
| 2 | Cricsheet extraction and 20-match hand audit |
| 3 | cohort flow, venue crosswalk, source-timing table |
| 4 | first half of pre-match reports and source-stated effect coding log |
| 5 | remaining reports and inter-coder sample |
| 6 | Elo, report-code merge, missingness audit |
| 7 | descriptive analysis and frozen feature/split manifest |
| 8 | logistic models, interactions, marginal effects |
| 9 | RF/XGBoost, calibration, bootstrap CIs, SHAP |
| 10 | paper, appendix, reproducibility run, revision |

For the accelerated SSAC27 milestone, follow `docs/ssac27_submission_plan.md` while preserving the same broad-cohort protocol and leakage rules.

## What to build next

The current repository has already progressed beyond the original Gate 2 starting point. The next high-value work is to finish the independent reliability gate for the 228 verified reports, continue outcome-blind source collection where useful, and then freeze the source-stated pitch-effect handling before the locked test is scored.

## Definition of a strong student paper

The paper does not need a new algorithm. Its sophistication comes from a precise question, honest scope, careful measurement, temporal validation, leakage prevention, uncertainty/calibration, transparent source-stated coding, reproducible artifacts, and clear limits on causal interpretation.
