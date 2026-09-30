# Research Question and Introduction

## Submission title

*What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket*

## Current primary research question

> Among men's ODIs, how many additional first-ten-over runs are associated with the same modeled match win probability as losing one additional wicket, and how does that run-wicket exchange rate vary with innings order, pre-match team strength, and prior venue scoring environment?

In plain language: **What is a powerplay wicket worth in runs, and does that value change with match context?** The estimand solves $p(R+d,W+1,C)=p(R,W,C)$ for the nonnegative, bounded run increment $d$, at 47 runs and a change from one to two wickets. It is an observational model-based exchange rate, not a causal or universal price. Only supported finite roots are reported; undefined roots are not zero.

The amended-source release covers 942 clean men's ODI matches (1,884 paired innings), 2015–2024: 871 matches/1,742 innings for development through 2023 and 71/142 for untouched 2024 temporal validation. A six-interaction L2 logistic model is primary. The corrected release yields only three finite roots among 18 supported contexts; the other 15 are undefined. At neutral pre-match Elo and median prior venue scoring, the one-to-two-wicket contrast at 47 runs is −10.505 percentage points batting first and −15.690 points chasing. The paired first-minus-chase difference is +5.185 points (95% CI −0.457 to +11.182), which includes zero. These results do not establish an innings-order difference.

The model's 2024 ROC-AUC is 0.6626 (95% CI 0.5461–0.7681), log loss 0.6726, and Brier score 0.2368; it did not improve AUC or log loss over the additive benchmark. Pitch measurements are excluded from this analysis; no pitch-interaction claim is approved. No 2025+ match outcomes were loaded or scored. The exact numeric release is controlled by `docs/ssac27_numeric_handoff.md`; current submission navigation and evidence status are in `docs/ssac27_submission_source_of_truth.md`.

## Claim boundary

Use associational language. Do not describe the exchange rate as causal, universal, or a coaching rule. A root outside development support or without a valid uncertainty interval is not a publishable finite price. Do not make pitch-measurement claims from this analysis.

## Historical research question and introduction (superseded)

The material below records the former aggression-and-pitch-centered framing. It is preserved for provenance, not as the current question, title, findings, or submission scope.

### Historical title

*What Makes a Successful ODI Powerplay? The Role of Aggression, Wicket Preservation, Opposition Strength, and Source-Stated Pitch Effects*

### Historical question

> Among men's One Day International cricket matches, how are powerplay aggression and wicket preservation associated with the batting team's probability of winning after accounting for pre-match team strength, innings order, toss, venue, year, and competition type—and, within the subgroup with verified pre-match pitch reports, how do those associations vary by **pitch effects explicitly stated by the source before the match**?

### Historical introduction

The first 10 overs of a One Day International can shape the remainder of a match, but runs alone do not define a successful powerplay. Aggression creates scoring value while wickets preserve the resources needed for the remaining 40 overs. The balance also depends on context: the same score can carry a different meaning against a stronger opponent, while chasing, or when a pre-match report explicitly expects seam, spin, easy batting, or inconsistent pace. Universal benchmarks such as “50 runs is a good powerplay” therefore discard information needed to evaluate an early-innings performance.

This study asks one connected question in two stages. First, the full modern ODI cohort estimates which combinations of powerplay runs, wickets, boundary-ball percentage, and dot-ball percentage are associated with winning after adjustment for pre-match team strength and match context. Second, the subgroup with source- and timing-verified pre-match pitch reports tests prespecified effect modification: whether the best balance of aggression and wicket preservation changes across **source-stated** batting-friendly, pace/seam, spin, balanced, and slow or two-paced expectations. The pitch-report analysis is therefore not a separate finding or a replacement cohort; it refines the full-cohort result.

Cricsheet ball-by-ball data provide the powerplay measures for all eligible men's ODIs from 2015 through a fixed snapshot. Leakage-safe pre-match Elo, innings order, toss, venue history, year, and competition type form the contextual adjustment set. Eligible pitch reports are timestamp-checked against scheduled starts and standardized without reading match outcomes. **The researchers do not diagnose the pitch themselves:** physical descriptions such as dry, grassy, moist, hard, cracked, worn, or used are retained only as provenance unless the source explicitly states the expected playing effect.

Nested logistic and nonlinear models, chronological train-validation-test periods, whole-match clustered confidence intervals, calibration analysis, and marginal predictions were planned to control overfitting and preserve paired-innings structure. This historical plan is not the current analysis or submission claim.
