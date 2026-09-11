# Paper Outline

This outline is for the full paper. The SSAC27 abstract is a focused extract with actual results from the same broad modern-ODI design, not a separate World-Cup-only study. Its separate plan is in `docs/ssac27_submission_plan.md`.

## Current drafting status

The cohort, powerplay extraction, pre-match team and venue histories,
chronological model table, 2024 validation, uncertainty estimates, and preliminary
figures are reproducible.
`docs/results.md` contains the current quantitative narrative and
`docs/limitations.md` fixes its interpretation boundary. Pitch-report collection,
source-timing verification, inter-coder reliability, pitch-adjusted models, and the
single locked-test evaluation remain incomplete. No current paragraph may present
the study as pitch-adjusted or final.

## Title page and abstract (200–250 words)

- One-sentence background.
- Research question and observational design.
- Data sources, sample period, and unit of analysis.
- Main models and chronological test.
- Two or three quantitative findings with confidence intervals.
- Main limitation and conclusion without causal language.

## 1. Introduction

1. Explain why the first 10 overs are strategically important in ODIs.
2. Explain why the same score can have different meaning across pitch behavior and innings order.
3. Identify the gap: early performance is often summarized without jointly addressing conditions, prior team strength, temporal validation, and calibration.
4. State the primary question and hypotheses.
5. Summarize contributions: reproducible extraction, audited pitch-behavior coding, chronological model comparison, uncertainty/calibration.

## 2. Background and related work

- ODI powerplay rules and strategic role.
- Cricket outcome prediction and common features.
- Environmental/pitch influences and measurement challenges.
- Why random splits overstate real-world performance when sports data evolve over time.
- Difference between explanation, association, and prediction.

Use academic or authoritative sources. Do not pad this section with generic machine-learning definitions.

## 3. Data and methods

### 3.1 Study cohort

- dates/events/gender;
- competition-type distribution and the role of World Cups as one subgroup;
- inclusion/exclusion rules;
- cohort flow diagram;
- final match and team-innings counts.

### 3.2 Cricsheet extraction

- JSON version/snapshot/checksum;
- exact first-10-over definitions;
- audit and edge cases.

### 3.3 Pitch reports

- source eligibility and timing;
- codebook and categories;
- double coding and reliability.

### 3.4 Limited non-pitch conditions

- why generic hourly weather is excluded from the primary design;
- how explicitly reported pre-match dew is handled as a secondary condition;
- why blank dew coding means unstated rather than absent.

### 3.5 Context and strength

- toss/innings order/venue/year;
- leakage-safe Elo and same-date batching.
- rolling prior-20 venue scoring proxy, same-date batching, coverage, and cold starts;

### 3.6 Statistical analysis

- feature sets and prespecified interactions;
- logistic, Random Forest, XGBoost;
- chronological training/tuning/test;
- metrics, calibration, match-cluster bootstrap CIs;
- feature importance, SHAP, marginal probabilities.

### 3.7 Reproducibility and ethics

- source terms/licences and attribution;
- transformation log and code/environment;
- handling of copyrighted prose via short paraphrase/citation;
- no individual-player ranking or sensitive data.

## 4. Results

### 4.1 Cohort and data quality

- row counts, exclusions, missingness, and join coverage;
- report current pitch coverage as 41/1,094 (3.74771%), with 109 of 150 reviewed matches set aside;
- report inter-coder reliability only after independent double coding.

### 4.2 Descriptive results

- distributions and correlations;
- observed win rates by powerplay runs/wickets and conditions.

### 4.3 Logistic associations

- coefficients/odds ratios with uncertainty;
- marginal predicted probabilities;
- interaction plots and interpretation.

### 4.4 Predictive performance

- report the completed 2024 validation metrics and clustered intervals as
  preliminary model-selection evidence;
- report locked-test metrics only after the pitch and model freeze gates pass;
- include calibration plots and avoid claiming success from accuracy alone.

### 4.5 Nonlinear interpretation

- permutation importance;
- SHAP summary/dependence;
- disagreements with logistic model.

### 4.6 Sensitivity analyses
- historical venue-condition sensitivity versus M1;
- report which conclusions changed and which remained stable.

## 5. Discussion

1. Direct answer to the research question.
2. Cricket interpretation of the largest associations/interactions.
3. Why nonlinear models did or did not improve held-out prediction.
4. Calibration and practical meaning.
5. Comparison with prior work.
6. Limitations: observational confounding, source coverage, subjective pitch coding, within-match pitch change, sample size, rule/era differences, paired innings dependence, and generalizability.
7. Future work: more eras/events, actual on-field timestamps/sensors, hierarchical venue/team models, external replication.

## 6. Conclusion

One short paragraph. Answer the question, give the practical/statistical takeaway, and keep the claim associational.

## Appendices

- complete data dictionary;
- pitch codebook and reliability matrices;
- exclusions and join audit;
- hyperparameter grids;
- full metrics/CIs;
- robustness tables;
- source and software manifests;
- preliminary result provenance in `docs/results.md`;
- fixed caveats and external blockers in `docs/limitations.md`;
- extra calibration and SHAP plots.
