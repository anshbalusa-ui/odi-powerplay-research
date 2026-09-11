# Preliminary Modeling Status

## Scope and lock state

This is a full-cohort preliminary analysis with a leakage-safe historical venue
proxy, but **without source-coded match-day pitch reports in the fitted models**.
Prior-20 venue history is available for 997 of 1,094 primary matches. A separate
audited merge now recognizes 28 provisional pitch-report matches, but that subset
remains too small and has not passed independent double-coding. No pitch coefficient
or pitch interaction is therefore estimated in the published preliminary models.

The fixed Cricsheet snapshot contributes 1,094 primary matches and 2,188 team-innings:

| Split | Dates | Matches | Team-innings | Use |
|---|---|---:|---:|---|
| development | 2015-01-01–2023-12-31 | 871 | 1,742 | fit preprocessing and models |
| validation | 2024-01-01–2024-12-31 | 71 | 142 | preliminary temporal evaluation |
| locked test | 2025-01-01–snapshot cutoff | 152 | 304 | untouched; not scored |

Both innings from each match remain in the same split. The frozen model-table SHA-256
is `ba1e541232568036ac4262f1660f419d236736c51a6b5af12016a8f949da6685`.

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
   innings order. Prespecified pitch interactions activate only in the audited
   pitch-complete model set.
7. `scoring_process_sensitivity`: M0 plus wickets, boundary-ball percentage, and
   dot-ball percentage, without runs or run rate.
8. `random_forest_challenger`: constrained nonlinear model on context, runs,
   wickets, boundary percentage, and dot-ball percentage.
9. `xgboost_challenger`: shallow regularized boosted trees on the same predictors.

No specification contains both `pp_runs` and deterministic `pp_run_rate`. Outcome,
final-score, result, and source-prose fields are rejected by the feature allowlist.
The locked-test partition helper records only locked match IDs and does not access
its outcome field.

Expanding rolling-origin diagnostics train on all earlier years and validate
separately on 2021, 2022, and 2023. Every fold refits imputation, scaling, and
encoding using only its training years. No hyperparameter search was performed;
the declared settings are prespecified rather than selected on 2024.

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
overfitting or temporal instability; it does not show that match-day surface
conditions are unimportant, and no source-coded pitch interpretation is possible.

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

Generated model binaries, hashes, validation predictions, calibration bins, and
metric JSON remain under `artifacts/` and are ignored by Git under the project's
rights/release policy. The training manifest records the input/configuration hashes,
package version, exact features, model-artifact hashes, and `locked_test_scored=false`.
Do not score the 2025–2026 locked test until model choices, pitch handling, and the
analysis plan are frozen.
