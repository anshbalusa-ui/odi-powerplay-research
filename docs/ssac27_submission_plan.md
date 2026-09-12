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

> What makes a successful ODI powerplay after accounting for opposition strength and match context, and—among matches with verified pre-match reports—when does pitch type change the best balance of aggression and wicket preservation?

The practical output is one coherent framework rather than two unrelated findings: a full-cohort description of successful powerplay profiles and a prespecified pitch-subgroup effect-modification analysis showing when the profile changes.

## Minimum viable SSAC analysis

### Required

- auditable Cricsheet extraction for all eligible men's ODIs from 2015 through the fixed data snapshot;
- competition-type labels, with World Cups used only as a subgroup check;
- complete cohort/exclusion flow;
- leakage-safe pre-match Elo difference;
- innings order and toss context;
- verified source timing and a lean, source-audited, match-specific pitch representation;
- baseline plus interpretable logistic model;
- one nonlinear challenger only after the logistic analysis is stable;
- chronological evaluation with development through 2023, validation in 2024, and 2025 through the fixed 2026 snapshot held out;
- ROC-AUC, log loss, Brier score, calibration, and match-clustered confidence intervals;
- one pitch-adjusted win-probability figure;
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

The pitch requirement is **not met**: 65 of 1,094 matches have timing-verified
AI-assisted first-pass codes, 160 of 225 reviewed matches are set aside, and
independent double coding has not occurred. The hand-audit worksheet is generated
but still needs external scorecard reconciliation.
The 2025–2026 locked test remains correctly unscored.

Go/no-go decision: the full-cohort powerplay result and verified-pitch subgroup must remain visibly nested under one research question. Do not submit a pitch effect-modification estimate until source coverage and independent reliability gates pass. If those gates are not met, retain the full-cohort result as Finding 1 and label the pitch analysis incomplete rather than implying that most matches had pitch adjustment. Never manufacture pitch labels from live/post-match commentary or unlock test outcomes to compensate for missing pitch data.

## September 5–October 1 sprint

| Dates | Deliverable | Go/no-go test |
|---|---|---|
| Sep 5–8 | download/extract Cricsheet; freeze broad modern-ODI cohort; hand-audit powerplays | no unresolved extraction discrepancies |
| Sep 9–13 | Elo, venue crosswalk, and source-timing audit | no future information in feature audit |
| Sep 14–18 | pitch-source collection/coding and reliability check | adequate source coverage or documented reduced pitch scope |
| Sep 19–22 | merge, missingness report, descriptive analysis, frozen split | 2025–snapshot test IDs locked and untouched |
| Sep 23–25 | logistic model, selected interactions, marginal predictions | interpretable and calibrated baseline comparison |
| Sep 26–27 | nonlinear challenger, bootstrap confidence intervals, final figures | identical held-out rows across models |
| Sep 28 | freeze results and repository snapshot | results reproduce from a clean run |
| Sep 29–30 | write and revise sub-500-word abstract | all claims backed by frozen outputs |
| Oct 1 | final rules check and submit before 11:59 p.m. ET | repository public and links verified |

## Scope fallback ladder

If pitch collection becomes the bottleneck, reduce complexity transparently rather than using post-match information:

1. simplify the pitch code to a smaller, high-reliability set of dimensions;
2. use only reports with verified publication times and add an explicit missing indicator;
3. define a prespecified, stratified pitch-analysis subset that spans years and competition types;
4. make individual sparse pitch dimensions secondary while retaining the high-coverage primary pitch category.

Never fill missing pre-match pitch descriptions using post-match reports.

## Abstract shell

### Introduction

State the industry problem, the inadequacy of raw powerplay benchmarks, and the exact question.

### Methods

State the cohort and sources, unit of analysis, leakage cutoff, conditions/context variables, chronological split, model types, and calibration/uncertainty methods.

### Results

Report sample size, the main 2024 validation association with uncertainty, and one
calibration result. Replace these with locked-test values only after every freeze
gate passes; never label validation estimates as final held-out performance.

### Conclusion

State the full-cohort powerplay finding first. Add the verified-pitch effect-modification finding only if coverage and reliability gates pass; otherwise identify it as the prespecified incomplete subgroup analysis rather than reframing the paper as pitch-adjusted.

## Submission-day checklist

- title plus body is 499 words or fewer;
- all four required headings are present;
- no promised or placeholder results;
- no causal claim from observational evidence;
- no more than two combined figures/tables;
- numbers match frozen repository outputs;
- repository is public and opens without authentication;
- data/source licences and attributions are visible;
- installation and reproduction instructions work from a clean environment;
- links in the form and abstract are correct;
- final submission occurs before the Eastern Time deadline.
