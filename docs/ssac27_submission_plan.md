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

> What makes a successful ODI powerplay after accounting for opposition strength and match context, and—among matches with verified pre-match reports—when do **pitch effects explicitly stated by those sources** change the best balance of aggression and wicket preservation?

The practical output is one coherent framework rather than two unrelated findings: a full-cohort description of successful powerplay profiles and a prespecified subgroup analysis using standardized source-stated pre-match pitch expectations.

**Measurement rule:** the project performs no independent pitch diagnosis. It does not infer spin from dryness, seam from grass/moisture, batting ease from hardness/flatness, or slow/two-paced behavior from wear/usage unless the eligible pre-match source explicitly states that expected playing effect. Physical surface descriptions may be retained as provenance only.

## Minimum viable SSAC analysis

### Required

- auditable Cricsheet extraction for all eligible men's ODIs from 2015 through the fixed data snapshot;
- competition-type labels, with World Cups used only as a subgroup check;
- complete cohort/exclusion flow;
- leakage-safe pre-match Elo difference;
- innings order and toss context;
- verified source timing and a lean, source-audited, match-specific representation of **explicitly stated pre-match pitch effects**;
- explicit-source-only re-audit of every legacy pitch code used in the final analysis;
- baseline plus interpretable logistic model;
- one nonlinear challenger only after the logistic analysis is stable;
- chronological evaluation with development through 2023, validation in 2024, and 2025 through the fixed 2026 snapshot held out;
- ROC-AUC, log loss, Brier score, calibration, and match-clustered confidence intervals;
- one source-stated-pitch-effect interaction figure if re-audit/reliability/coverage gates pass;
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

Go/no-go decision: the full-cohort powerplay result and verified-pitch-report
subgroup must remain visibly nested under one research question. Do not submit an
interaction estimate as a final reliability-cleared finding until:

1. the compliant source-stated reference set is frozen;
2. independent reliability passes on at least 20% of that set;
3. coder reconciliation and agreement reporting are complete; and
4. the ten-match pitch-subgroup validation design is judged adequate or replaced by
   a prespecified alternative.

Until then, retain the full-cohort result as Finding 1 and label the compliant
pitch fit as a reproducible checkpoint. Never manufacture a pitch effect from
physical surface wording, venue reputation, live/post-match commentary, or later
outcomes, and never unlock test outcomes to compensate for missing pitch data.

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

If compliant pitch-effect coverage becomes the bottleneck, reduce complexity transparently rather than inferring missing effects:

1. simplify the source-stated effect code to a smaller, high-reliability set of dimensions;
2. use only reports/codes that pass timing and explicit-source-support checks;
3. define a prespecified, stratified pitch-report subgroup that spans years and competition types;
4. make individual sparse source-stated dimensions secondary while retaining the higher-coverage compliant primary source-stated category.

Never fill missing pre-match pitch effects using post-match reports, venue history, or researcher interpretation of physical pitch descriptions.

## Abstract shell

### Introduction

State the industry problem, the inadequacy of raw powerplay benchmarks, and the exact question.

### Methods

State the cohort and sources, unit of analysis, leakage cutoff, contextual variables, chronological split, model types, and calibration/uncertainty methods. Explicitly state that final pitch variables are standardized from **source-stated pre-match expectations**, not independent researcher assessment of the surface.

### Results

Report a pitch-subgroup result only as a reproducibility checkpoint unless the
independent reliability gate, reconciliation, and sample-size review pass. Never
present the legacy 228-code smoke-test metrics as a final pitch result.

### Conclusion

State the full-cohort powerplay finding first. Add the verified-pitch-report
interaction finding only if the compliant source-stated dataset, independent
reliability, reconciliation, and sample-size gates pass; otherwise identify it as
the prespecified incomplete subgroup analysis rather than reframing the paper as
pitch-adjusted.

## Submission-day checklist

- title plus body is 499 words or fewer;
- all four required headings are present;
- no promised or placeholder results;
- no causal claim from observational evidence;
- pitch variables used in results have passed explicit-source-only re-audit;
- pitch variables are described as standardized source statements, not researcher pitch diagnosis;
- no pitch interaction is presented as final before independent reliability and reconciliation;
- no more than two combined figures/tables;
- numbers match frozen repository outputs;
- repository is public and opens without authentication;
- data/source licences and attributions are visible;
- installation and reproduction instructions work from a clean environment;
- links in the form and abstract are correct;
- final submission occurs before the Eastern Time deadline.
