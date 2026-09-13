# Limitations and External Blockers

## Current evidence boundary

The implemented analysis is results-complete for a full-cohort 2024 temporal
validation that includes a historical venue-scoring proxy and a separate
re-audited 229-match pitch subgroup checkpoint. It is not a reliability-cleared
final pitch-report result, not locked-test performance, and not causal evidence.
The 2025–2026 outcome lock must remain closed until the independent reliability
gate and final model choices are frozen.

## Match-data coverage and selection

- Cricsheet is the immutable ball-by-ball source, but its ODI archive may not cover
  every ODI played. Results generalize first to matches represented in the fixed
  snapshot.
- The primary cohort excludes ties, no-results, incomplete first 10 overs, matches
  without two regulation innings, and DLS/revised-target matches. This creates a
  clean estimand but may select a different match mix from all ODIs.
- Cricsheet metadata supplies dates rather than reliable scheduled start timestamps
  for the pitch-source timing decision. A separately verified UTC start-time table
  is required before a pitch report is eligible.
- Automated invariant checks found zero issues across 2,188 primary innings, but
  the 24-innings worksheet still requires independent reconciliation against an
  external scorecard. Automated agreement is not a substitute for that audit.

## Outcome and dependence structure

Each decided match contributes one winning-team innings and one losing-team innings,
so the row-level outcome prevalence is structurally 50%. The two rows are not
independent. Chronological splits keep match pairs together and uncertainty resamples
whole matches, but ordinary logistic point estimates still describe a team-innings
representation rather than independent matches. A paired-match sensitivity analysis
remains advisable.

The 2024 validation set contains only 71 matches. Its model confidence intervals are
wide, especially for calibration and nonlinear models. Point-estimate rankings should
not be treated as stable league tables.

## Pre-match team strength

- Elo and prior-20 win rates use only earlier match dates and batch all same-day
  updates, preventing same-day ordering leakage.
- Date batching sacrifices any real within-day ordering that verified start times
  could provide.
- Elo uses fixed initial rating 1500 and K-factor 20. These are transparent design
  choices, not uniquely correct cricket-strength parameters.
- Cold starts and limited prior histories remain for emerging teams. Missing rolling
  win rates are imputed inside training data rather than reconstructed from future
  matches.
- The strength features do not directly encode roster availability, injuries,
  rankings, travel, or home advantage beyond other context fields.

## Historical venue-condition proxy

- Venue histories use only the most recent 20 matches at the exact Cricsheet venue
  name on strictly earlier dates. Same-day matches are batched.
- Coverage is 997 of 1,094 primary matches; 97 venue cold starts rely on
  development-fitted missing-value handling.
- Ground-name changes, spelling variants, and multiple playing areas within one
  venue can fragment or pool histories imperfectly.
- Earlier powerplay scoring reflects teams, opponents, eras, weather, and match
  conditions as well as the ground. It is a predictive context proxy, not a
  measurement of the prepared surface for the target match.
- The venue-history sensitivity model did not improve 2024 AUC, log loss, or Brier
  score over M1 by point estimate. Wide overlapping intervals preclude a strong
  negative conclusion.

## Pre-match pitch reports and ESPNcricinfo

Current reproducible source/timing coverage is **243 of 1,094 primary matches
(22.212066%)**. All 243 are non-ESPN, match-specific pre-match reports with
verified publication timing. The strict re-audited analytical release contains
229 rows; 14 legacy rows whose sources could not be re-opened are excluded.
No row has passed the independent-human reliability gate.

### Strict measurement boundary

The project performs **no independent pitch diagnosis**. Final analytical pitch
variables may represent only expected playing effects explicitly stated by
eligible pre-match sources. Physical descriptions such as dry, dusty, grassy,
green, moist, hard, cracked, worn, tacky, or used may be preserved in a short
paraphrase for provenance, but they cannot be converted by researcher judgment
into `spin`, `pace_seam`, `batting_ease`, `bounce_profile`, or
`two_paced_expected` values.

For example, a dry surface is not coded as spin-supportive unless the source
itself states expected spin/turn/grip assistance. A grassy surface is not coded
as pace/seam-supportive unless the source itself states the expected pace/seam
effect. If the source does not state a playing effect, that effect remains
blank or `unknown`.

The first 228 codes were re-audited against their eligible sources. The registry
records 169 `passed_revised`, 45 `passed_unchanged`, and 14
`source_unavailable` legacy rows; the 15 current-standard rows remain
`current_standard`. Unsupported inferred effects were blanked or removed.
Source-unavailable rows are not silently treated as `unknown` and do not enter
the compliant model table.

Therefore:

- the strict 229-row release and its 458-row model table are reproducible
  source-stated-effect analysis inputs;
- the 2024 pitch validation has only ten match clusters and is a sample-size
  checkpoint, not a definitive interaction finding;
- its locked 2025–2026 partition remains reserved and unscored;
- no fitted pitch model is a reliability-cleared final claim until an
  independent second coder codes the prespecified sample and agreement is
  reconciled and reported.

ESPNcricinfo's reviewed terms prohibit the automated extraction approach
originally contemplated for data mining. The project therefore does not bulk
scrape ESPN text. Live commentary and post-match reports are also analytically
ineligible because they contain information observed after the pre-match
prediction timestamp. Eligible ESPN material can be collected manually or
through licensed access.


Cricsheet documents its numeric IDs as generally, but not invariably, matching
Cricinfo IDs. The 1,094 generated ESPN links are therefore unfetched navigation
candidates, not collected ESPN data. A candidate must be reconciled against teams,
date, event, and venue before any report can pass source validation.

The full tracked start-time template covers 1,094 matches with `pending` placeholders.
The separate tracked verified release contains 243 cited scheduled starts, one for
each currently published pre-match report row. Collectors need to verify only rows
with collected pitch reports, not the entire cohort. The audit validates cohort
identity, provenance, IANA timezones, and exact local-to-UTC conversion. Downstream
code exposes only rows explicitly marked `verified`, so a blank, partial, or merely
plausible timestamp cannot make a pitch source eligible.

The outcome-blind queue contains 1,094 match-specific search tasks and no result or
powerplay columns. Twenty-four outcome-blind batches reviewed 600 matches: 243
passed source/timing gates, 357 are explicitly listed in
`data/manual/pitch_set_aside.csv`, and 494 remain unreviewed. The verified report
subset covers 22.212066% of the cohort. Its 40.5% yield among reviewed matches is
not representative of the full cohort; source discoverability and publication
practices vary by competition, era, and team.

The compliant release is complete for the legacy re-audit gate. Remaining
requirements for a final pitch-effect result are:

1. human collection or a licensed source-access route for any ESPN material added later;
2. a direct eligible pre-match URL and publication timestamp for each coded match;
3. a verified scheduled match-start UTC timestamp;
4. short original paraphrases rather than copied report prose;
5. a second independent coder for at least 20% of the 229-row compliant reference set;
6. reconciliation and reliability reporting before treating pitch interactions as
   final research claims.

The accepted reports span 35 normalized provider hostnames, but the source mix is
not uniform: the largest provider contributes 24.3% and the top three contribute
50.2%. The provider HHI is 1,131. Provider-level category and confidence counts
for the 243-row auditable input release are descriptive provenance summaries;
the compliant category counts are reported separately because 14
source-unavailable rows are excluded.

Pitch-report availability is likely nonrandom across teams, venues, competitions,
years, and publishers. Complete-case pitch-report models may therefore be
selection-biased even after coverage and provider reporting. Text-to-code
standardization also introduces measurement error and coder subjectivity. Missing
pitch effects must remain missing; they cannot be backfilled from live commentary,
match outcomes, generic venue stereotypes, physical surface descriptors,
researcher cricket knowledge, historical venue scoring, or post-match descriptions.

## Modeling limitations

- The current hyperparameters are prespecified. Rolling-origin folds provide
  diagnostics for 2021–2023, but no broad hyperparameter search was conducted.
- Venue one-hot encoding is high-dimensional and may contribute to temporal
  overfitting when unseen or sparsely represented grounds appear in validation.
- The 2024 powerplay-only benchmark outperformed richer context models by point
  estimate. This may reflect overfitting, temporal drift, or limited validation
  size; it does not prove context is irrelevant.
- Logistic relationships are linear on the log-odds scale except for prespecified
  interactions. Spline/quadratic run effects and paired-match alternatives remain
  sensitivity analyses.
- Random Forest and XGBoost are constrained challengers. Their weaker 2024 results
  do not justify SHAP interpretation or final-test promotion at this stage.
- Calibration bins can be sparse. Whole-match bootstrap intervals are shown, but
  bin-level estimates remain noisy.

## Reproducibility and redistribution

Raw and derived datasets, model binaries, predictions, and generated figures are
ignored by Git and rebuilt locally from source manifests. This avoids silently
redistributing third-party data, but means a repository clone must download the
fixed source snapshot and rerun the pipeline. The run manifest records hashes and
package versions; timestamps in run metadata intentionally vary between executions.

The code's MIT licence does not relicense Cricsheet data or source-report content.
Any public release of derived match data, pitch notes, or model artifacts requires a
separate rights review and the applicable source attribution.
