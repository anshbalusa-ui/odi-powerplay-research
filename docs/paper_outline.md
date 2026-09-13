# Paper Outline

This outline is for the full paper. The SSAC27 abstract is a focused extract with actual results from the same broad modern-ODI design, not a separate World-Cup-only study. Its separate plan is in `docs/ssac27_submission_plan.md`.

## Current drafting status

The cohort, powerplay extraction, pre-match team and venue histories,
chronological model table, 2024 validation, uncertainty estimates, preliminary
figures, and the 228-match source- and timing-verified pitch-report collection are
reproducible. `docs/results.md` contains the current quantitative narrative and
`docs/limitations.md` fixes its interpretation boundary.

The 228 existing analytical pitch codes are **provisional legacy codes** created
under an earlier codebook. They must be re-audited against the current
explicit-source-only rule before the project can call them final source-stated
pitch-effect variables. The current legacy-code model is only a pipeline smoke test;
independent double-coding and the locked-test evaluation also remain incomplete.

## Title page and abstract (200–250 words)

- Use the working title *What Makes a Successful ODI Powerplay? The Role of Aggression, Wicket Preservation, Opposition Strength, and Source-Stated Pitch Effects*.
- One-sentence background and unified research question.
- Data sources, sample period, and match-clustered unit of analysis.
- Finding 1: full-cohort powerplay profiles after contextual adjustment.
- Finding 2: effect modification by **pitch effects explicitly stated in eligible pre-match sources**, only after legacy-code re-audit and reliability gates pass.
- Main limitation and conclusion without causal language.

## 1. Introduction

1. Explain why aggression and wicket preservation jointly define an ODI powerplay.
2. Explain why opposition strength, innings order, and source-stated pre-match pitch behavior can change the meaning of the same start.
3. Identify the gap: early performance is often summarized without jointly addressing context, temporal validation, and calibration.
4. State one research question with a full-cohort analysis and a prespecified verified-pitch-report effect-modification subgroup.
5. Summarize contributions without presenting the subgroup as an unrelated second paper.

## 2. Background and related work

- ODI powerplay rules and strategic role.
- Cricket outcome prediction and common features.
- Pre-match pitch-report measurement challenges and source heterogeneity.
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

### 3.3 Verified-pitch-report subgroup

- prespecified role as an effect-modification analysis;
- source eligibility, timing, codebook, coverage, and cohort comparison;
- **explicit-source-only rule:** the coder standardizes only playing effects explicitly stated by the source and performs no independent pitch diagnosis;
- physical descriptions such as dry, grassy, moist, hard, cracked, worn, or used remain provenance only unless the source itself explicitly states the playing effect;
- legacy 228-code re-audit before final pitch modeling;
- independent double coding and reliability gate after the compliant reference set is frozen.

### 3.4 Limited non-pitch conditions

- why generic hourly weather is excluded from the primary design;
- how explicitly reported pre-match dew is handled as a secondary condition;
- why blank dew coding means unstated rather than absent.

### 3.5 Context and strength

- toss/innings order/venue/year;
- leakage-safe Elo and same-date batching;
- rolling prior-20 venue scoring proxy, same-date batching, coverage, and cold starts;
- venue history is a scoring-environment sensitivity and is not treated as match-day pitch evidence.

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
- no researcher-inferred pitch labels from physical surface descriptions;
- no individual-player ranking or sensitive data.

## 4. Results

### 4.1 Cohort and data quality

- row counts, exclusions, missingness, and join coverage;
- report pre-match source/timing coverage as 228/1,094 (20.840951%), with 347 of 575 reviewed matches set aside and 519 unreviewed;
- report how many of the 228 remain analytically compliant after explicit-source-only re-audit;
- report the 35-provider source mix and inter-coder reliability only after the compliant reference set and independent double coding are complete.

### 4.2 Finding 1: full-cohort powerplay profiles

- distributions and correlations for runs, wickets, boundary-ball percentage, and dot-ball percentage;
- adjusted associations and marginal win probabilities for aggression and wicket preservation;
- innings-order modification and chronological predictive performance.

### 4.3 Finding 2: modification by source-stated pitch effects

- restrict to source- and timing-verified reports whose analytical codes also pass the explicit-source-only re-audit;
- report subgroup composition, selection differences, and reliability before estimates;
- show prespecified runs × source-stated effect and wickets × source-stated effect marginal predictions;
- make clear that categories are standardized publisher/source expectations, not researcher diagnoses of the physical pitch;
- interpret as refinement of Finding 1, not an independent headline claim.

### 4.4 Predictive performance

- report the completed full-cohort 2024 validation metrics and clustered intervals as preliminary model-selection evidence;
- treat existing legacy pitch-code smoke-test metrics as reproducibility evidence only;
- report final pitch-subgroup and locked-test metrics only after re-audit, reliability, and model freeze gates pass;
- include calibration plots and avoid claiming success from accuracy alone.

### 4.5 Nonlinear interpretation

- permutation importance;
- SHAP summary/dependence;
- disagreements with logistic model.

### 4.6 Sensitivity analyses

- historical venue-scoring sensitivity versus M1;
- report which conclusions changed and which remained stable;
- never use physical pitch descriptors or venue history to backfill missing source-stated pitch effects.

## 5. Discussion

1. Answer what makes a successful powerplay using the full-cohort result.
2. Explain when that answer changes using the compliant verified-pitch-report/source-stated-effect result, if its gates pass.
3. Keep both findings under the same aggression-versus-wicket-preservation question.
4. Explain why nonlinear models did or did not improve held-out prediction.
5. Discuss calibration and practical meaning.
6. Limitations: observational confounding, pitch-report subgroup selection and coverage, source wording differences, legacy-code re-audit, coding reliability, within-match pitch change, rule/era differences, paired innings dependence, and generalizability.
7. Future work: more eras/events, direct instrumented/on-field surface measurements, hierarchical venue/team models, external replication.

## 6. Conclusion

One short paragraph. Answer the question, give the practical/statistical takeaway, and keep the claim associational.

## Appendices

- complete data dictionary;
- source-stated pitch-effect codebook and reliability matrices;
- legacy-code re-audit record;
- exclusions and join audit;
- hyperparameter grids;
- full metrics/CIs;
- robustness tables;
- source and software manifests;
- preliminary result provenance in `docs/results.md`;
- fixed caveats and external blockers in `docs/limitations.md`;
- extra calibration and SHAP plots.
