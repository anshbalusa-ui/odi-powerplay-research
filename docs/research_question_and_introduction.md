# Research Question and Introduction

## Working title

*What Is a Good ODI Powerplay? Conditions-Adjusted Associations Between First-10-Over Performance and Match Outcomes*

## Final research question

> Among men's One Day International cricket matches, how are runs scored and wickets lost during the first 10 overs associated with the batting team's probability of winning after accounting for pre-match team strength, opponent strength, innings order, toss, venue, year, pitch characteristics, and weather—and how do these associations vary across different playing conditions?

## Introduction

The first 10 overs of a One Day International can shape the remainder of a match, but a raw powerplay score does not have the same meaning in every setting. A rapid start on a flat, dry surface may be routine, while the same number of runs on a damp or seam-friendly pitch may represent a major advantage. Wickets also change the value of early scoring: two teams can finish the powerplay with similar run totals but face very different risks for the remaining 40 overs. Simple benchmarks such as “50 runs is a good powerplay” therefore ignore much of the context needed to evaluate early-innings performance.

This study investigates the association between first-10-over batting performance and match outcomes across men's ODIs. Cricsheet ball-by-ball data are used to calculate powerplay runs, wickets, boundary-ball percentage, dot-ball percentage, and contextual match variables. Pre-match pitch descriptions are coded through a documented and auditable framework, while hourly historical weather estimates provide continuous measures of temperature, humidity, precipitation, cloud cover, wind speed, and dew point. The main cohort includes all eligible men's ODIs from 2015 through a fixed data snapshot, covering bilateral series and major or qualifying tournaments rather than restricting the analysis to World Cups.

A central challenge is confounding by team quality. Stronger teams are more likely both to produce effective powerplays and to win, so an unadjusted relationship could overstate what the first 10 overs reveal. The analysis therefore begins with a leakage-safe pre-match baseline containing team-strength difference and other information known before or by the prediction time. Powerplay runs and wickets are then added in nested models to estimate their incremental association with win probability. Interactions test whether those associations change with pitch, weather, and innings order. Chronological train, validation, and test periods, match-clustered confidence intervals, calibration analysis, and interpretable logistic and nonlinear models are used to reduce overfitting and make the results reproducible.

Because the data are observational, the paper will not claim that powerplay performance causes victory. Its goal is to quantify a conditions-adjusted association and produce a more useful benchmark for analysts, broadcasters, coaches, and viewers: not merely how many runs a team scored, but how strong that start appears given wickets, opposition quality, and the conditions in which it occurred.

## Claim boundary

Use language such as **associated with**, **related to**, **incremental predictive value**, and **estimated win probability**. Do not use **caused**, **led to**, or **effect of** unless a future design supports causal identification.
