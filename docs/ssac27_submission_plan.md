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

> How much does the value of an ODI powerplay start change after accounting for wickets, opposition strength, innings order, pitch, and early-match weather?

The practical output is a conditions-adjusted benchmark that estimates whether a start was stronger or weaker than its raw score suggests. This gives broadcasters, analysts, and teams a more useful interpretation than a universal rule such as “50/1 is a good powerplay.”

## Minimum viable SSAC analysis

### Required

- auditable Cricsheet extraction for all eligible men's ODIs from 2015 through the fixed data snapshot;
- competition-type labels, with World Cups used only as a subgroup check;
- complete cohort/exclusion flow;
- leakage-safe pre-match Elo difference;
- innings order and toss context;
- verified venue coordinates, scheduled start times, and start-hour weather;
- a manageable, source-audited pitch representation;
- baseline plus interpretable logistic model;
- one nonlinear challenger only after the logistic analysis is stable;
- chronological evaluation with development through 2023, validation in 2024, and 2025 through the fixed 2026 snapshot held out;
- ROC-AUC, log loss, Brier score, calibration, and match-clustered confidence intervals;
- one conditions-adjusted win-probability figure;
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

## September 5–October 1 sprint

| Dates | Deliverable | Go/no-go test |
|---|---|---|
| Sep 5–8 | download/extract Cricsheet; freeze broad modern-ODI cohort; hand-audit powerplays | no unresolved extraction discrepancies |
| Sep 9–13 | Elo, venue crosswalk, start times, weather | no future information in feature audit |
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
4. make pitch-conditioned analysis secondary while retaining weather/context in the broad primary model.

Never fill missing pre-match pitch descriptions using post-match reports.

## Abstract shell

### Introduction

State the industry problem, the inadequacy of raw powerplay benchmarks, and the exact question.

### Methods

State the cohort and sources, unit of analysis, leakage cutoff, conditions/context variables, chronological split, model types, and calibration/uncertainty methods.

### Results

Report sample size, the main adjusted relationship or interaction with uncertainty, final held-out metrics versus baseline, and one calibration result. Do not fill this section until outputs are frozen.

### Conclusion

State the conditions-adjusted cricket insight, the practical application, and the observational limitation.

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
