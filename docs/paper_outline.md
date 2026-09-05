# Paper Outline

## Title page and abstract (200–250 words)

- One-sentence background.
- Research question and observational design.
- Data sources, sample period, and unit of analysis.
- Main models and chronological test.
- Two or three quantitative findings with confidence intervals.
- Main limitation and conclusion without causal language.

## 1. Introduction

1. Explain why the first 10 overs are strategically important in ODIs.
2. Explain why the same score can have different meaning across pitch/weather and innings order.
3. Identify the gap: early performance is often summarized without jointly addressing conditions, prior team strength, temporal validation, and calibration.
4. State the primary question and hypotheses.
5. Summarize contributions: reproducible extraction, audited pitch coding, leakage-safe weather, chronological model comparison, uncertainty/calibration.

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

### 3.4 Weather

- venue coordinates/timezones;
- Open-Meteo variables and reanalysis limitation;
- start-hour timing rule and sensitivity window.

### 3.5 Context and strength

- toss/innings order/venue/year;
- leakage-safe Elo and same-date batching.

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

- row counts, exclusions, missingness, join coverage, pitch-coding reliability.

### 4.2 Descriptive results

- distributions and correlations;
- observed win rates by powerplay runs/wickets and conditions.

### 4.3 Logistic associations

- coefficients/odds ratios with uncertainty;
- marginal predicted probabilities;
- interaction plots and interpretation.

### 4.4 Predictive performance

- test metrics with CIs versus baselines;
- calibration plots;
- avoid claiming success from accuracy alone.

### 4.5 Nonlinear interpretation

- permutation importance;
- SHAP summary/dependence;
- disagreements with logistic model.

### 4.6 Sensitivity analyses

- report which conclusions changed and which remained stable.

## 5. Discussion

1. Direct answer to the research question.
2. Cricket interpretation of the largest associations/interactions.
3. Why nonlinear models did or did not improve held-out prediction.
4. Calibration and practical meaning.
5. Comparison with prior work.
6. Limitations: observational confounding, source coverage, subjective pitch coding, weather resolution/timing, sample size, rule/era differences, paired innings dependence, and generalizability.
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
- extra calibration and SHAP plots.

