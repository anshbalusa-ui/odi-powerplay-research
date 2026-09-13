# Limitations and External Blockers

## Current evidence boundary

The implemented analysis is results-complete for a full-cohort 2024 temporal
validation that includes a historical venue-scoring proxy but not the final
source-stated match-specific pre-match pitch-effect analysis. It is not a final
pitch-report-subgroup result, not locked-test performance, and not causal evidence.
The 2025–2026 outcome lock must remain closed until the compliant source-stated
pitch-effect dataset and final model choices are frozen.

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
verified publication timing. The first 228 analytical pitch codes are
**provisional legacy codes created under an earlier codebook** and have not yet
passed the current explicit-source-only re-audit. The 15 batch-24 rows were coded
under the current rule. No row has passed the independent-human reliability gate.

### Strict measurement boundary

The final project performs **no independent pitch diagnosis**. Final analytical
pitch variables may represent only expected playing effects explicitly stated by
eligible pre-match sources. Physical descriptions such as dry, dusty, grassy,
green, moist, hard, cracked, worn, tacky, or used may be preserved in a short
paraphrase for provenance, but they cannot be converted by researcher judgment into
`spin`, `pace_seam`, `batting_ease`, `bounce_profile`, or `two_paced_expected`
values.

For example, a dry surface is not coded as spin-supportive unless the source itself
states expected spin/turn/grip assistance. A grassy surface is not coded as
pace/seam-supportive unless the source itself states the expected pace/seam effect.
If the source does not state a playing effect, that effect remains blank or
`unknown`.

Because the first 228 codes predate this stricter rule, every retained nonblank
pitch-effect value in those rows must be checked back against its eligible source.
Any value based only on a physical descriptor or analyst cricket knowledge must be
blanked or removed. Only after that re-audit may the project describe the compliant
legacy values as source-stated pitch effects.

Therefore:

- the existing mixed-status 243-code complete-case model fit is a pipeline smoke test only;
- its runs × pitch and wickets × pitch interactions cannot support a research claim;
- no fitted provisional-code model can be called reliably adjusted for source-stated
  pitch effects;
- no source-stated match-day pitch-effect conclusion should appear in an abstract or
  paper result until the re-audit, reliability, and sample-size gates pass.

ESPNcricinfo's reviewed terms prohibit the automated extraction approach originally
contemplated for data mining. The project therefore does not bulk scrape ESPN text.
Live commentary and post-match reports are also analytically ineligible because they
contain information observed after the pre-match prediction timestamp. Eligible ESPN
material is limited to individually cited pre-match previews or pitch reports that
can be collected manually or through licensed access.

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

Completing the final pitch-effect layer still requires:

1. an explicit-source-only re-audit of all retained legacy codes;
2. removal/blanking of any value based only on physical descriptors or analyst inference;
3. human collection or a licensed source-access route for any ESPN material added later;
4. a direct eligible pre-match URL and publication timestamp for each coded match;
5. a verified scheduled match-start UTC timestamp;
6. short original paraphrases rather than copied report prose;
7. a second independent coder for at least 20% of the compliant reference set;
8. reconciliation and reliability reporting before final outcome modeling.

The accepted reports span 35 normalized provider hostnames, but the source mix is
not uniform: the largest provider contributes 24.3% and the top three contribute
50.2%. The provider HHI is 1,131. Provider-level category and confidence counts
from the provisional mixed-status release remain useful for source-distribution
auditing but should not be interpreted as final source-stated category counts until
the re-audit is complete.

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
