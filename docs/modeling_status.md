# Preliminary Modeling Status

## Scope and lock state

This is a full-cohort preliminary analysis with a leakage-safe historical venue
proxy. The main fitted models still exclude source-stated match-specific pre-match
pitch effects. The audited merge now recognizes 228 provisional pitch-report matches,
but independent double-coding has not passed and only ten of those matches fall in
the 2024 validation year. Interactions with source-stated pitch effects are therefore
a pipeline smoke test, not a published research result.

**Measurement rule:** pitch-report variables standardize only expected playing effects explicitly stated by eligible pre-match sources. The researchers do not independently diagnose the surface and do not infer spin from dryness, pace/seam from grass or moisture, batting ease from hardness/flatness, or slow/two-paced behavior from wear/usage unless the source itself states that effect.

The fixed Cricsheet snapshot contributes 1,094 primary matches and 2,188 team-innings:

| Split | Dates | Matches | Team-innings | Use |
|---|---|---:|---:|---|
| development | 2015-01-01–2023-12-31 | 871 | 1,742 | fit preprocessing and models |
| validation | 2024-01-01–2024-12-31 | 71 | 142 | preliminary temporal evaluation |
| locked test | 2025-01-01–snapshot cutoff | 152 | 304 | untouched; not scored |

Both innings from each match remain in the same split. The current 228-pitch merged
model-table SHA-256 is
`a8e3d33301d93b61001a572ddb3a73f8f501654531b58aeef40052f181cb757e`.

## Specifications

All models use fixed settings and development-only preprocessing. Numeric missing
values use a development-fitted median plus missingness indicators; numeric values
are standardized. Categorical missing values use the development mode and unseen
validation levels are ignored by one-hot encoding. Penalized logistic regression
uses L2 penalty, `C=1.0`, and `liblinear`. The constrained Random Forest uses 500
trees, depth 6, and minimum leaf size 20. The shallow XGBoost challenger uses 400
trees, depth 3, learning rate 0.05, subsampling 0.8, and minimum child weight 10.
Every stochastic estimator uses seed `20250905` and one worker for reproducibility.

1. `intercept_only`: development prevalence.
2. `m0_pre_match`: pre-match Elo difference, prior experience and prior-20 win
   rates, innings order, toss, venue, rule era, year, and competition type.
3. `powerplay_benchmark`: powerplay runs and wickets only.
4. `m1_context_powerplay`: M0 plus powerplay runs and wickets.
5. `venue_history_powerplay_sensitivity`: M1 plus the availability and sample size
   of the rolling prior-20-match venue history and its earlier-match powerplay runs,
   wickets, boundary percentage, and dot-ball percentage.
6. `m2_prespecified_interactions`: M1 plus runs × innings order and wickets ×
   innings order. Prespecified interactions with **source-stated pitch effects** activate only in the audited
   pitch-report-complete model set.
7. `scoring_process_sensitivity`: M0 plus wickets, boundary-ball percentage, and
   dot-ball percentage, without runs or run rate.
8. `random_forest_challenger`: constrained nonlinear model on context, runs,
   wickets, boundary percentage, and dot-ball percentage.
9. `xgboost_challenger`: shallow regularized boosted trees on the same predictors.

No specification contains both `pp_runs` and deterministic `pp_run_rate`. Outcome,
final-score, result, source-prose fields, raw physical surface descriptors, and any researcher-inferred pitch labels are rejected by the feature allowlist.
The locked-test partition helper records only locked match IDs and does not access
its outcome field.

Expanding rolling-origin diagnostics train on all earlier years and validate
separately on 2021, 2022, and 2023. Every fold refits imputation, scaling, and
encoding using only its training years. No hyperparameter search was performed;
the declared settings are prespecified rather than selected on 2024.

## Provisional verified-pitch-report subset

The expanded pitch-report merge contains 456 paired team-innings from 228 matches:
334 development rows from 167 matches, 20 validation rows from ten 2024 matches,
and 102 unscored locked-test rows from 51 matches. A separate smoke-test fit used
only this complete-case subset and activated the prespecified **source-stated pitch-effect** main fields
and powerplay × source-stated-effect interactions. Because there are no verified-pitch-report matches in
2021, its explicitly requested rolling-origin diagnostics use 2022 and 2023 only;
the missing year is not silently represented as a fold.

On the ten-match 2024 subset, the runs-and-wickets benchmark had ROC-AUC 0.69,
log loss 0.6305, and Brier score 0.2206. M1 with context, source-stated pitch main effects, and
powerplay had ROC-AUC 0.48, log loss 0.8289, and Brier score 0.3101. M2 with the
prespecified source-stated pitch interactions had ROC-AUC 0.57, log loss 0.7693, and Brier score
0.2907. These values are too unstable for substantive interpretation: the
validation set has only ten independent match clusters, source coverage is
selected, and no independent double-coding exists. The locked 2025–2026 outcomes
remain untouched.

Only 27 of 167 development matches have an observed `dew_expected` code, so any
dew coefficient remains sparse and uninterpretable. Generated pitch-report-model artifacts
use separate `pitch_` paths and do not replace the full-cohort validation artifacts.

## 2024 temporal-validation results

Point estimates below use 142 team-innings from 71 matches. Intervals are 95%
percentile intervals from 2,000 whole-match cluster-bootstrap resamples with seed
`20250905`; all 2,000 resamples were valid.

| Model | ROC-AUC (95% CI) | Log loss (95% CI) | Brier score (95% CI) | Accuracy |
|---|---:|---:|---:|---:|
| intercept only | 0.500 (0.500–0.500) | 0.693 (0.693–0.693) | 0.250 (0.250–0.250) | 0.500 |
| M0 pre-match | 0.588 (0.456–0.709) | 0.701 (0.619–0.790) | 0.252 (0.216–0.290) | 0.563 |
| powerplay benchmark | 0.740 (0.642–0.822) | 0.613 (0.566–0.668) | 0.212 (0.190–0.237) | 0.697 |
| M1 context + powerplay | 0.708 (0.597–0.809) | 0.625 (0.536–0.724) | 0.218 (0.181–0.260) | 0.641 |
| venue-history + powerplay sensitivity | 0.705 (0.594–0.806) | 0.625 (0.536–0.724) | 0.219 (0.181–0.260) | 0.648 |
| M2 interactions | 0.710 (0.597–0.809) | 0.627 (0.537–0.730) | 0.219 (0.181–0.261) | 0.655 |
| scoring-process sensitivity | 0.703 (0.590–0.805) | 0.626 (0.537–0.725) | 0.220 (0.182–0.261) | 0.634 |
| constrained Random Forest | 0.644 (0.527–0.753) | 0.672 (0.649–0.694) | 0.239 (0.228–0.250) | 0.620 |
| shallow XGBoost | 0.641 (0.524–0.748) | 0.685 (0.595–0.784) | 0.243 (0.205–0.284) | 0.606 |

Calibration intercept/slope are saved with the same cluster-bootstrap intervals.
The intercept-only slope is correctly reported as unidentifiable because every
prediction is constant. These validation results are preliminary model-selection
evidence, not locked-test performance and not causal estimates. In this 2024 sample,
the two-variable powerplay benchmark outperformed the higher-dimensional context
models and both nonlinear challengers. Adding historical venue conditions to M1
did not improve ROC-AUC, log loss, or Brier score by point estimate. This suggests
overfitting or temporal instability; it does not show that source-stated match-specific
pitch effects are unimportant, and the venue proxy cannot be interpreted as pitch evidence.

## Reproduction

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
# macOS only: brew install libomp
.venv/bin/python scripts/build_team_strength.py
.venv/bin/python scripts/build_venue_conditions.py
.venv/bin/python scripts/build_model_table.py
.venv/bin/python scripts/train_models.py --fit-without-locked-test
.venv/bin/python scripts/evaluate_models.py
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/reproduce.py --skip-download
```

For the provisional pitch-report-subset smoke test:

```bash
.venv/bin/python scripts/train_models.py \
  --fit-without-locked-test \
  --input data/processed/model_team_innings_pitch.csv \
  --model-dir artifacts/models/pitch_validation_frozen \
  --predictions-output artifacts/tables/pitch_validation_predictions.csv \
  --manifest-output artifacts/models/pitch_validation_frozen/manifest.json \
  --rolling-origin-output artifacts/tables/pitch_rolling_origin_metrics.json \
  --rolling-validation-years 2022 2023
.venv/bin/python scripts/evaluate_models.py \
  --input artifacts/tables/pitch_validation_predictions.csv \
  --metrics-output artifacts/tables/pitch_validation_metrics.json \
  --calibration-output artifacts/tables/pitch_validation_calibration.csv
```

Generated model binaries, hashes, validation predictions, calibration bins, and
metric JSON remain under `artifacts/` and are ignored by Git under the project's
rights/release policy. The training manifest records the input/configuration hashes,
package version, exact features, model-artifact hashes, and `locked_test_scored=false`.
Do not score the 2025–2026 locked test until model choices, source-stated pitch-effect handling, and the
analysis plan are frozen.
