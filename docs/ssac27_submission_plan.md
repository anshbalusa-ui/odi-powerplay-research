# SSAC27 Submission Plan

## Role in the project

The MIT Sloan Sports Analytics Conference 2027 Research Papers Competition is a near-term milestone for this research, not its only target. The broader ODI paper will continue after the abstract deadline and can expand the sample, features, and sensitivity analyses.

## Official submission constraints

As checked on September 5, 2026, the official competition page states:

- abstract due October 1, 2026 at 11:59 p.m. Eastern Time;
- fewer than 500 words, including title and body;
- at most two tables or figures combined;
- required sections: Introduction, Methods, Results, and Conclusion;
- results must be actual, not promised;
- evaluation emphasizes novelty, academic rigor, reproducibility, application, and impact;
- an open-source repository link supporting the research is required;
- cricket belongs in the Other Sports track.

Official page: https://www.sloansportsconference.com/research-paper-competition

Recheck the page immediately before submission in case instructions change.

## Focused contribution

Avoid framing the study as only another match-winner classifier. The stronger applied question is:

> What makes a successful ODI powerplay after accounting for opposition strength and match context, and—among matches with verified pre-match reports—do **model-estimated expected playing conditions** alter the aggression/wicket-preservation associations?

The full-cohort result remains Finding 1; the new pitch-expectation measurement is a nested subgroup extension. The historical source-stated effects and human-recoding plan are retained as provenance, **not** inputs to the new assessments.

**Amended measurement rule (2026-09-27):** permit bounded inference from source-grounded, reviewed pre-match text; preserve uncertainty, outcome blindness and independent model-assessment stability. Never present estimated expectations as actual pitch truth. See `docs/pitch_expectation_method.md`.

## Minimum viable SSAC analysis

### Required

- auditable Cricsheet extraction for all eligible men's ODIs from 2015 through the fixed data snapshot;
- competition-type labels, with World Cups used only as a subgroup check;
- complete cohort/exclusion flow;
- leakage-safe pre-match Elo difference;
- innings order and toss context;
- verified source timing and an independently reviewed original-text, outcome-blind measurement of pre-match expected conditions;
- frozen new rubric, three independent passes, mechanical consensus and small human evidence audit before any new pitch-outcome interpretation;
- baseline plus interpretable logistic model;
- one nonlinear challenger only after the logistic analysis is stable;
- chronological evaluation with development through 2023, validation in 2024, and 2025 through the fixed 2026 snapshot held out;
- ROC-AUC, log loss, Brier score, calibration, and match-clustered confidence intervals;
- one expected-environment interaction figure only if new measurement viability, human approval and unlocked outcome analysis justify it;
- one compact model-performance/calibration table or figure;
- public repository with code, data-building instructions, permitted data, manifests, and results.

### Defer until after the abstract if necessary

- historical pre-2015 ODI expansion and era-comparison models;
- large interaction grids;
- many competing nonlinear models;
- exhaustive SHAP panels;
- women’s ODI expansion;
- full manuscript prose and extensive appendices.

Deferral means sequencing, not abandonment.

## Current readiness gate

As of the reproducible September 2026 run, the Cricsheet cohort, automated metric
audit, pre-match team strength, prior-20 venue histories covering 997 of 1,094
matches, chronological splits, six logistic specifications, two constrained
nonlinear challengers, rolling-origin diagnostics, 2024 validation, clustered
uncertainty, calibration, and preliminary figures are complete. The venue-history
sensitivity did not improve M1's 2024 AUC or proper scores by point estimate. The
current numeric narrative is in `docs/results.md`.

The 200-match **source/timing coverage** target is exceeded: 243 of 1,094 matches
have eligible non-ESPN pre-match reports and verified scheduled starts, 357 of 600
reviewed matches are set aside, and 494 remain unreviewed. The explicit-source-only
re-audit is complete: 169 legacy rows are `passed_revised`, 45 are
`passed_unchanged`, and 14 are `source_unavailable`; 15 batch-24 rows are
`current_standard`. The strict analytical release contains 229 matches.
Independent double coding remains incomplete. The 2025–2026 locked test remains
correctly unscored.

Go/no-go decision: retain the full-cohort result as Finding 1. Historical
human coding and reconciliation remain incomplete; the legacy pitch fit is not
a final finding. The new expected-environment construct was amended **before**
final pitch-outcome interpretation. Its measurement gate requires reviewed
pre-match source text, blinded A/B/C assessments, frozen prompt and hashes,
mechanical agreement and confidence diagnostics, sparse development/2024
category counts and a human sanity-audit worksheet. **Stop for human approval
at that gate.** No pitch Finding 2 or pitch figure is promised without a
viable measured sample and subsequent unlocked analysis. The 2025+ outcome
lock cannot compensate for missing source content.

## Pre-reliability prep run

The reproducible prep branch now has canonical, machine-readable outputs for the
unlocked 2015–2024 cohort: 942 matches and 1,884 team-innings, with 71 matches
and 142 innings in 2024 validation. The fixed runs-and-wickets benchmark reached
validation ROC-AUC 0.740 (95% match-clustered interval 0.642–0.822); the
context-plus-powerplay model reached 0.708 and the prespecified interaction model
0.710. A fixed model-standardized contrast was +0.082 across 38 to 57 runs at
two wickets and −0.126 across one to two wickets at 47 runs; both are
observational, not causal.

The branch also adds an independent unlocked-cohort audit, exact pitch sparsity
tables, a raw-preserving reliability/reconciliation workflow, a gated pitch
interaction plan with reconciled-release hash provenance, a 499-word abstract
validator, and a validated abstract skeleton. Pitch interaction estimates remain
blocked: the outcome-blind pitch subset has 178 unlocked matches, 150 reported
sparse cells at the diagnostic threshold, and no submitted second-coder
judgments or completed reconciliation. The locked 2025+ outcomes remain
unscored and absent from these evidence outputs.


## September 5–October 1 sprint

| Dates | Deliverable | Go/no-go test |
|---|---|---|
| Sep 5–8 | download/extract Cricsheet; freeze broad modern-ODI cohort; hand-audit powerplays | no unresolved extraction discrepancies |
| Sep 9–13 | Elo, venue crosswalk, source-timing audit, pitch-report collection | no future information in feature audit |
| Sep 14–18 | independent reliability coding + reconciliation | compliant pitch reference set frozen and reliability reported |
| Sep 23–25 | logistic model, selected interactions, marginal predictions | interpretable and calibrated baseline comparison |
| Sep 26–27 | nonlinear challenger, bootstrap confidence intervals, final figures | identical held-out rows across models |
| Sep 28 | freeze results and repository snapshot | results reproduce from a clean run |
| Sep 29–30 | write and revise sub-500-word abstract | all claims backed by frozen outputs |
| Oct 1 | final rules check and submit before 11:59 p.m. ET | repository public and links verified |

## Scope fallback ladder

If new expectation measurement or sample viability is the bottleneck, reduce scope transparently rather than inventing coverage:

1. keep the full-cohort powerplay result as Finding 1 if new expectation measurement is not viable;
2. after independent model-assessment stability and source-content review,
   simplify the new categorical modifier only on pre-outcome semantic/sparse
   cell evidence, never on appealing associations;
3. treat the pitch extension as exploratory when the new 2024 validation or
   development categories cannot support prespecified interactions.

Never fill missing expected conditions using post-match reports, venue
history, old pitch labels, or unsupported researcher inference.

## Abstract shell

### Introduction

State the industry problem, the inadequacy of raw powerplay benchmarks, and the exact question.

### Methods

State the cohort, sources, unit of analysis, leakage cutoff, contextual variables, chronological split, model types, and calibration/uncertainty methods. If pitch results are actually approved, call their variables **model-estimated pre-match expected playing conditions**, not observed or true pitch behavior.

### Results

Report a new pitch-subgroup result only after actual model assessments,
mechanical stability diagnostics, human source/evidence audit, human approval
and unlocked outcome analysis. Never present historical strict-code fits
or synthetic technical smoke assessments as final pitch results.

### Conclusion

State the full-cohort powerplay finding first. Add a new expectation-modified
pitch finding only if the new measurement gate, human approval and subsequent
unlocked pitch analysis support it; otherwise say that pitch expectations
remain an incomplete prespecified subgroup extension.

## Submission-day checklist

- title plus body is 499 words or fewer;
- all four required headings are present;
- no promised or placeholder results;
- no causal claim from observational evidence;
- new expectation variables are derived only from newly reviewed, pre-match source evidence, not historical coded labels;
- pitch variables are described as uncertain pre-match expectations, not physical pitch truth;
- no new pitch interaction is presented as final before three blinded passes, mechanical stability diagnostics, human evidence audit and approval;
- no more than two combined figures/tables;
- numbers match frozen repository outputs;
- repository is public and opens without authentication;
- data/source licences and attributions are visible;
- installation and reproduction instructions work from a clean environment;
- links in the form and abstract are correct;
- final submission occurs before the Eastern Time deadline.
