# Preliminary Results

## Status

These are reproducible **development and 2024 temporal-validation results**, not
final paper results. The 2025–2026 test period remains locked and its outcomes have
not been scored. The intended pitch-report result is a prespecified effect-modification
analysis nested within the same powerplay question, not a separate finding.

The project has 243 source- and timing-verified pre-match reports, exceeding the
collection target. The explicit-source-only re-audit is complete: 169 legacy
rows are `passed_revised`, 45 are `passed_unchanged`, and 14 are
`source_unavailable`; the 15 batch-24 rows are `current_standard`. The strict
analytical release contains 229 rows and excludes the 14 unavailable sources.
Independent double-coding must still pass before a pitch interaction is treated
as a final reliability-cleared result.

The current measurement rule is strict: analytical pitch variables may standardize
only expected playing effects explicitly stated by eligible pre-match sources.
Physical descriptions such as dry, dusty, grassy, green, moist, hard, cracked,
worn, tacky, or used are provenance only unless the source itself explicitly states
the corresponding playing effect. The researchers do not independently diagnose
the pitch.

## Cohort construction

The fixed Cricsheet ODI snapshot contains 3,182 matches and 6,283 extracted
team-innings. The cleaning rules retain 2,742 decided, two-regulation-innings core
matches and exclude 440 matches. Nonexclusive reasons include DLS/revised targets
(266), no-results (121), incomplete first-10-over innings (72), matches without two
regulation innings (81), and ties (34).

The primary modern cohort contains 1,094 men's ODIs from 2015 onward and 2,188
team-innings. It includes 592 bilateral-series, 279 qualification-pathway, 110 World
Cup, 50 multi-team-series, 28 other-ODI, 20 Champions Trophy, and 15 continental-cup
matches. World Cups remain a 110-match subgroup, not a replacement for the primary
cohort.

Automated metric auditing checked all 2,188 primary rows and all 1,094 match pairs.
It found zero formula, range, innings-pair, or outcome-label issues. The separate
24-innings hand-audit worksheet spans 12 matches and every year from 2015 through
2026; independent scorecard reconciliation is still required.

## First-10-over performance

Every retained primary innings contains exactly 60 legal powerplay deliveries.
Across the 2,188 innings, teams scored 106,391 runs and lost 3,158 wickets in the
first 10 overs. Boundary and dot percentages use legal-ball denominators; byes,
leg-byes, and non-boundary fours are not boundary balls, while wides and no-balls
are excluded from the legal-ball denominator under the documented definitions.

| Measure | Overall mean | Median | Range | Batting-first mean | Chasing mean |
|---|---:|---:|---:|---:|---:|
| powerplay runs | 48.62 | 47 | 9–118 | 46.82 | 50.43 |
| powerplay wickets | 1.44 | 1 | 0–7 | 1.38 | 1.51 |
| boundary-ball percentage | 11.29% | 11.67% | 0.00–35.00% | 10.76% | 11.82% |
| dot-ball percentage | 65.74% | 66.67% | 26.67–91.67% | 66.71% | 64.77% |

The ball-weighted totals are 14,821 boundary balls and 86,304 dot balls among
131,280 legal balls, equal to 11.29% and 65.74%, respectively. These are descriptive
associations; innings order, opposition, venue, era, and match state differ across
rows.

## Pre-match venue-history proxy

An outcome-blind venue table uses the most recent 20 matches at the exact recorded
venue, restricted to strictly earlier match dates. It summarizes prior powerplay
runs and wickets per innings plus ball-weighted boundary and dot-ball percentages.
Same-day matches share the same pre-date state and do not update one another.

At least one prior venue match is available for 997 of 1,094 primary matches
(91.13%); 97 matches are cold starts. This is a historical scoring-environment
proxy, not a direct observation of the match-day surface, weather, preparation, or
curator intent, and it cannot replace or infer missing source-stated pre-match pitch
effects.

## Chronological model evaluation

Models fit 1,742 development rows from 871 matches dated 2015–2023. Preliminary
performance uses 142 rows from 71 matches in calendar year 2024. Confidence
intervals are 95% percentile intervals from 2,000 whole-match cluster-bootstrap
resamples with seed `20250905`. Preprocessing is fit only on each training set.

| Model | ROC-AUC (95% CI) | Log loss (95% CI) | Brier score (95% CI) | Accuracy |
|---|---:|---:|---:|---:|
| intercept only | 0.500 (0.500–0.500) | 0.693 (0.693–0.693) | 0.250 (0.250–0.250) | 0.500 |
| M0 pre-match | 0.588 (0.456–0.709) | 0.701 (0.619–0.790) | 0.252 (0.216–0.290) | 0.563 |
| powerplay runs + wickets | 0.740 (0.642–0.822) | 0.613 (0.566–0.668) | 0.212 (0.190–0.237) | 0.697 |
| M1 context + powerplay | 0.708 (0.597–0.809) | 0.625 (0.536–0.724) | 0.218 (0.181–0.260) | 0.641 |
| venue-history + powerplay sensitivity | 0.705 (0.594–0.806) | 0.625 (0.536–0.724) | 0.219 (0.181–0.260) | 0.648 |
| M2 prespecified interactions | 0.710 (0.597–0.809) | 0.627 (0.537–0.730) | 0.219 (0.181–0.261) | 0.655 |
| scoring-process sensitivity | 0.703 (0.590–0.805) | 0.626 (0.537–0.725) | 0.220 (0.182–0.261) | 0.634 |
| constrained Random Forest | 0.644 (0.527–0.753) | 0.672 (0.649–0.694) | 0.239 (0.228–0.250) | 0.620 |
| shallow XGBoost | 0.641 (0.524–0.748) | 0.685 (0.595–0.784) | 0.243 (0.205–0.284) | 0.606 |

The runs-and-wickets-only benchmark had the strongest 2024 point estimates. Adding
high-dimensional context reduced validation discrimination and worsened proper
scoring relative to that benchmark; the constrained nonlinear challengers also did
not improve it. Adding rolling venue-history conditions to M1 produced AUC 0.7052
versus 0.7082, log loss 0.6252 versus 0.6246, and Brier score 0.2185 versus
0.2183. These negligible-to-adverse point-estimate differences have wide,
overlapping intervals. They neither establish a useful venue-history contribution
nor imply anything about the importance of match-specific source-stated pitch
effects.

The M1 calibration intercept was -0.007 (95% CI -0.089 to 0.077) and slope was
0.767 (0.346 to 1.332). The runs-and-wickets benchmark calibration intercept was
0.175 (0.038 to 0.363) and slope was 1.399 (0.756 to 2.280). Calibration curves use
fixed probability bins with whole-match bootstrap uncertainty. The intercept-only
calibration slope is unidentifiable because its probabilities are constant.

## Compliant source-stated pitch-effect subgroup

The strict merged subset contains 229 matches and 458 paired innings: 168
development matches, ten 2024 validation matches, and 51 reserved locked-test
matches. The 14 legacy rows with unavailable sources are excluded. The locked
outcomes remain unscored. A separate complete-case fit confirms that the
re-audited source-stated pitch main fields and prespecified interactions execute
end to end.

On the ten-match 2024 validation subset, the 2,000 whole-match bootstrap point
estimates and 95% intervals were:

| Model | ROC-AUC (95% CI) | Log loss (95% CI) | Brier score (95% CI) |
|---|---:|---:|---:|
| powerplay benchmark | 0.670 (0.360–0.910) | 0.641 (0.459–0.835) | 0.225 (0.143–0.315) |
| M0 pre-match | 0.420 (0.040–0.760) | 0.906 (0.584–1.226) | 0.348 (0.209–0.487) |
| M1 context + powerplay | 0.540 (0.180–0.850) | 0.774 (0.487–1.054) | 0.288 (0.168–0.406) |
| M2 interactions | 0.580 (0.230–0.860) | 0.730 (0.479–0.980) | 0.275 (0.168–0.386) |

All bootstrap repetitions were valid. The ten independent validation matches
make these intervals wide; the values are reproducibility checkpoints, not
evidence that source-stated pitch effects improve prediction. Reliability remains
open pending the independent 20% second-coder sample and reconciliation.

## Interpretation boundary

The observable conclusion is limited: first-10-over runs and wickets contain useful
held-out information about the batting team's match outcome in the full 2024
sample. The study remains observational, so the estimates are associations rather
than causal effects.

The strict report/timing merge and compliant interaction pipeline run on the
229-match release. The legacy re-audit confirms that retained nonblank analytical
pitch values are source-stated or that the row is excluded when its source is
unavailable. Independent second-coder reliability is still pending. No ESPN page
text, live or post-match commentary entered a predictor, and no claim uses the
locked test period. Exact model definitions, hashes, and artifact paths are in
`docs/modeling_status.md`.
