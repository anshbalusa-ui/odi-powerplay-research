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

- Use the working title *What Makes a Successful ODI Powerplay? The Role of Aggression, Wicket Preservation, Opposition Strength, and Pitch Conditions*.
- One-sentence background and unified research question.
- Data sources, sample period, and match-clustered unit of analysis.
- Finding 1: full-cohort powerplay profiles after contextual adjustment.
- Finding 2: pitch effect modification in the source-verified subgroup, only after its gates pass.
- Main limitation and conclusion without causal language.

## 1. Introduction

1. Explain why aggression and wicket preservation jointly define an ODI powerplay.
2. Explain why opposition strength, innings order, and pitch behavior can change the meaning of the same start.
3. Identify the gap: early performance is often summarized without jointly addressing context, temporal validation, and calibration.
4. State one research question with a full-cohort analysis and a prespecified verified-pitch effect-modification subgroup.
5. Summarize contributions without presenting the subgroup as an unrelated second paper.

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

### 3.3 Verified-pitch subgroup

- prespecified role as an effect-modification analysis;
- source eligibility, timing, codebook, coverage, and cohort comparison;
- independent double coding and reliability gate.

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
- report current pitch coverage as 65/1,094 (5.94150%), with 160 of 225 reviewed matches set aside;
- report inter-coder reliability only after independent double coding.

### 4.2 Finding 1: full-cohort powerplay profiles

- distributions and correlations for runs, wickets, boundary-ball percentage, and dot-ball percentage;
- adjusted associations and marginal win probabilities for aggression and wicket preservation;
- innings-order modification and chronological predictive performance.

### 4.3 Finding 2: pitch effect modification

- restrict to source- and timing-verified pitch matches;
- report subgroup composition, selection differences, and reliability before estimates;
- show prespecified runs × pitch and wickets × pitch marginal predictions;
- interpret as refinement of Finding 1, not an independent headline claim.

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

1. Answer what makes a successful powerplay using the full-cohort result.
2. Explain when that answer changes using the verified-pitch effect-modification result, if its gates pass.
3. Keep both findings under the same aggression-versus-wicket-preservation question.
4. Explain why nonlinear models did or did not improve held-out prediction.
5. Discuss calibration and practical meaning.
6. Limitations: observational confounding, pitch-subgroup selection and coverage, subjective coding, within-match pitch change, rule/era differences, paired innings dependence, and generalizability.
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
