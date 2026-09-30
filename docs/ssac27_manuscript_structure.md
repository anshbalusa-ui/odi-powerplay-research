# SSAC27 Manuscript Structure

**Working title:** *What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket*

This file reorganizes the **existing current research** into a manuscript flow modeled on the pattern common to strong MIT Sloan Sports Analytics Conference papers and open-source finalist repositories: establish the sports decision problem early, state the contribution clearly, show the data and method transparently, surface actual results, validate them, then finish with practical interpretation and limitations.

It does **not** introduce new results or change the current claim boundary. Exact claims and numbers remain controlled by [`ssac27_submission_source_of_truth.md`](ssac27_submission_source_of_truth.md) and [`ssac27_numeric_handoff.md`](ssac27_numeric_handoff.md).

## Abstract

Use the required four-part competition structure:

1. **Introduction** — the run-wicket tradeoff question and why it matters in ODI decision-making.
2. **Methods** — cohort, model, bounded exchange-rate estimand, contextual variables, temporal validation, and whole-match uncertainty.
3. **Results** — supported finite roots, undefined contexts, fixed-run wicket-loss contrasts, paired interval, and 2024 model validation.
4. **Conclusion** — context dependence, support limits, and the observational/non-causal interpretation.

Current source: [`ssac27_abstract_skeleton.md`](ssac27_abstract_skeleton.md).

---

## 1. Introduction

### 1.1 The sports problem
Explain the basic strategic tension: powerplay runs create immediate scoring value while wickets preserve resources for the remaining innings.

### 1.2 Why a single benchmark is incomplete
Motivate why the same first-10-over score can imply different match positions depending on wickets and context.

### 1.3 Research question
State the current technical and plain-language questions exactly as controlled by the source of truth.

### 1.4 Contribution
Present the contribution as a **context-dependent, support-aware run-wicket exchange-rate framework on the modeled win-probability scale**, not as a universal wicket price.

### 1.5 Claim boundary
State early that the design is observational, pitch is excluded, unsupported roots are undefined rather than zero, and no 2025+ outcomes are opened or scored.

Primary source: [`research_question_and_introduction.md`](research_question_and_introduction.md).

---

## 2. Related Work and Positioning

Keep this section focused on what the paper adds rather than providing a generic machine-learning review.

### 2.1 ODI powerplay analytics and win prediction
Place the run-wicket tradeoff within prior cricket outcome and early-innings analytics.

### 2.2 Exchange-rate / decision-value framing
Explain how the paper differs from reporting raw coefficients, average run benchmarks, or a single global wicket value.

### 2.3 Context, temporal validation, and leakage
Position the study's strictly pre-match context construction and untouched temporal validation.

### 2.4 Research gap
State the specific gap the estimand addresses: a supported, contextual run increment that equates modeled win probability across adjacent wicket states.

Primary source: [`literature/ssac27_powerplay_tradeoff_prior_art.md`](literature/ssac27_powerplay_tradeoff_prior_art.md).

---

## 3. Data

### 3.1 Source and cohort
Describe the September 29 amended Cricsheet source, 2015–2024 study window, 942 clean matches / 1,884 paired innings, and the development/2024 temporal-validation split.

### 3.2 Unit of analysis
One batting-team innings per row; both innings from a match remain grouped in splits and resamples.

### 3.3 Powerplay variables
Define first-10-over runs, wickets, legal deliveries, and relevant extraction rules.

### 3.4 Pre-match context
Describe innings order, date-batched pre-match Elo, and strictly earlier-date prior venue scoring environment.

### 3.5 Exclusions and audit
Summarize inclusion/exclusion rules and the independent data audit.

Primary sources:
- [`ssac27_tradeoff_data_audit.md`](ssac27_tradeoff_data_audit.md)
- [`data_dictionary.md`](data_dictionary.md)
- [`sources.md`](sources.md)

---

## 4. Methods

### 4.1 Primary estimand
Define the bounded nonnegative (d) satisfying (p(R+d,W+1,C)=p(R,W,C)), with the primary contrast fixed at 47 runs and wickets 1→2.

### 4.2 Context grid and support
Explain the 18 prespecified primary contexts and the rule that a root must be finite, nonnegative, bracketed, and within development-data support.

### 4.3 Model specification
Describe the frozen six-interaction L2 logistic primary model and the additive/four-term comparators.

### 4.4 Uncertainty
Describe 1,000 whole-match development refits, conditional root intervals, same-refit paired comparisons, and the joint-validity gate for paired root-difference intervals.

### 4.5 Temporal validation
Describe the untouched 2024 set and 2,000 whole-match validation resamples for each frozen model.

### 4.6 Reproducibility controls
State the source hash, match grouping, leakage protections, locked 2025+ period, tests, independent QA, and release manifest.

Primary sources:
- [`ssac27_powerplay_tradeoff_protocol.md`](ssac27_powerplay_tradeoff_protocol.md)
- [`ssac27_tradeoff_statistical_spec.md`](ssac27_tradeoff_statistical_spec.md)
- [`ssac27_numeric_handoff.md`](ssac27_numeric_handoff.md)

---

## 5. Results

Lead with the answer to the research question, then show model-validation detail.

### 5.1 Supported run-wicket exchange rates
Report the three finite 1→2 roots and conditional intervals. Explicitly state that 15/18 contexts are undefined, not zero.

**Table 1:** the three-row finite-root table controlled by the submission source of truth.

### 5.2 Fixed-run wicket-loss effects
Report all supported fixed-run probability contrasts at 47 runs, emphasizing the neutral-Elo / median-venue examples.

### 5.3 Context comparison
Report the paired first-minus-chase wicket-loss probability difference and its interval; do not claim an innings-order difference when the interval includes zero.

### 5.4 Temporal validation
Report the primary, additive, and four-term 2024 AUC/log-loss/Brier results. State directly that the primary does not improve held-out AUC or log loss.

### 5.5 Figure
Use the corrected Figure 1 only after the existing rights/release condition is satisfied. The figure should visually distinguish all supported fixed-run probability losses from the much smaller subset of finite roots.

Primary sources:
- [`ssac27_submission_source_of_truth.md`](ssac27_submission_source_of_truth.md)
- [`ssac27_numeric_handoff.md`](ssac27_numeric_handoff.md)
- [`results.md`](results.md)

---

## 6. Robustness, Validation, and Falsification Checks

Keep this section separate from the headline results so rigor is visible without burying the main sports takeaway.

### 6.1 Comparator models
Additive and four-term specifications.

### 6.2 Alternate wicket contrasts
0→1 sensitivity and 2→3 sensitivity, clearly subordinate to the frozen 1→2 estimand.

### 6.3 Support and root validity
Show why undefined roots are a substantive result rather than missing values to be imputed.

### 6.4 Whole-match uncertainty
Explain why resampling occurs at the match level.

### 6.5 Independent QA
Summarize statistical/artifact QA, test coverage, compile checks, and release-integrity checks.

---

## 7. Practical Interpretation and Application

This section should answer the industry-facing question: **what can an analyst, coach, or decision-maker actually learn from the framework?**

- A single universal “good powerplay” or wicket price can hide meaningful context.
- The framework shows when a finite run-wicket compensation is supported and when the data/model do not support one.
- Fixed-run wicket-loss probability effects remain interpretable even when a finite exchange-rate root is undefined.
- Application should remain descriptive/decision-support oriented; the model does not prove that intentionally sacrificing a wicket causes a compensating win-probability change.

This section should make the application obvious without crossing the causal claim boundary.

---

## 8. Limitations

Keep limitations specific and technically meaningful:

- observational confounding;
- model dependence of the exchange-rate estimand;
- limited 2024 validation sample of 71 independent matches;
- support restrictions and conditional root intervals;
- calibration uncertainty;
- prior-venue scoring environment is historical context, not match-day pitch measurement;
- original September 10 archive unavailable;
- derived public artifacts/figures subject to third-party rights review;
- generalizability beyond the studied men's ODI period.

Primary source: [`limitations.md`](limitations.md).

---

## 9. Conclusion

Use one compact conclusion:

1. answer the question;
2. state that the exchange rate varies by context and is often unsupported as a finite value;
3. emphasize the framework's support-aware interpretation;
4. repeat that the estimates are observational rather than causal coaching rules.

---

## References

Use the literature review and source documentation to keep sports-domain references, methodological references, and data-source attribution distinct.

---

## Appendix / Reproducibility

Move detail here when it is necessary for auditability but distracts from the main paper narrative:

- full context grid;
- complete paired-comparison table;
- alternate 0→1 and 2→3 sensitivities;
- coefficient table;
- source and release hashes;
- extraction definitions;
- data audit detail;
- validation/bootstrap implementation detail;
- additional calibration diagnostics;
- full reproducibility commands;
- software/package information;
- rights/provenance notes.

The repository README and [`docs/README.md`](README.md) should remain the external reviewer's navigation layer; this manuscript structure should remain the writing layer.
