# Research Design and Analysis Plan

## 1. Study identity

**Working title:** *Early Advantage or Conditions? ODI Powerplay Performance and Win Probability Across Pitches and Weather*

**Design:** retrospective observational prediction/association study using ball-by-ball match data, manually coded pre-match pitch descriptions, and historical reanalysis weather.

**Claim boundary:** the study estimates conditional associations and predictive performance. It does not prove that scoring more quickly causes a win, because team quality, strategy, opposition, and other unmeasured factors influence both powerplay performance and the result.

## 2. Questions and hypotheses

### Primary question

How do first-10-over runs and wickets relate to the batting team's eventual win probability after accounting for pre-match pitch, early-match weather, team strength, opposition strength, toss, innings order, venue, and year?

### Prespecified hypotheses

- **H1:** Conditional on wickets and context, more powerplay runs are associated with higher win probability.
- **H2:** Conditional on runs and context, more powerplay wickets lost are associated with lower win probability.
- **H3:** The runs-win and wickets-win relationships vary across pitch categories.
- **H4:** Innings order modifies these relationships because the strategic meaning of a start differs when batting first versus chasing.

Weather interactions are exploratory unless the final protocol names a small number before looking at outcomes. Testing every possible interaction would create a multiple-comparisons problem.

## 3. Cohort and scope

### Recommended pilot

Men's ICC ODI World Cups in 2015, 2019, and 2023.

- Train and tune on 2015 and 2019 with rolling-origin folds.
- Use 2023 exactly once as the locked final test set.
- If the sample is too small for stable interaction estimates, present wide confidence intervals honestly and treat nonlinear models as exploratory.

### Primary inclusion criteria

- Cricsheet `match_type == "ODI"`.
- Requested gender and event/year scope.
- Two regulation innings.
- A decided winner.
- At least 60 legal balls in each analyzed powerplay for six-ball overs.
- Successfully validated match metadata.

### Primary exclusions

- Ties, no-results, abandoned matches, and matches without a winner.
- Super-over innings.
- Short/incomplete first-10-over windows.
- DLS/revised-target matches in the primary cohort, because interruption and target revision introduce difficult timing and comparability issues.
- Rows whose pre-match/source status cannot be verified when a variable requires pre-match availability.

All exclusions remain in an audit table with one or more reason codes. A sensitivity analysis can add DLS/revised matches with carefully defined indicators.

## 4. Units of analysis

### Primary: team-innings row

Each regulation innings creates one row. `batting_team_won` is 1 if that innings' batting team won and 0 if it lost. This answers: *after observing one team's first 10 overs, how strongly does that start relate to its final result?*

Two rows from the same match are statistically dependent. Therefore:

- both rows remain in the same fold and split;
- bootstrap samples draw whole matches, not individual rows;
- uncertainty estimates use match-clustered resampling or standard errors.

### Secondary: paired match row

Create a robustness dataset after both powerplays are complete:

- difference in powerplay runs;
- difference in wickets lost;
- difference in boundary and dot-ball percentages;
- outcome from a consistently defined team's perspective.

This avoids duplicate outcomes and answers a different question: *after both teams have completed ten overs, which powerplay advantage is associated with winning?*

## 5. Exact powerplay definitions

- **Window:** every delivery event in overs indexed 0 through 9.
- **Runs:** sum of `runs.total` across those delivery events, including delivery-level extras.
- **Legal ball:** a delivery without a wide or no-ball extra.
- **Run rate:** `runs * balls_per_over / legal_balls`.
- **Boundary ball:** a legal delivery with 4 or 6 batter runs and no `non_boundary` flag.
- **Boundary percentage:** 100 times boundary balls divided by legal balls.
- **Dot ball:** a legal delivery with zero total runs.
- **Dot-ball percentage:** 100 times dot balls divided by legal balls.
- **Wickets lost:** recorded dismissals except `retired hurt`.
- **Complete powerplay:** at least `10 * balls_per_over` legal balls in the window.

The extractor also saves delivery-event and legal-ball counts so every denominator can be audited.

## 6. Predictor timing and leakage rules

The prediction timestamp is the end of the focal batting team's tenth over. A candidate predictor is allowed only if it is available at or before that time.

| Allowed | Not allowed |
|---|---|
| Focal team's first-10-over score events | Any focal-team event after over 10 |
| Pre-match pitch report published before play | Post-match pitch summary or result article |
| Toss, batting order, teams, venue, date | Player-of-match, victory margin, final totals |
| Team ratings computed only from earlier dates | End-of-year ranking or tournament-final rating |
| Weather at scheduled start hour | Full match-day mean using later hours |
| Year and prior history | Statistics calculated using the test/future period |

Cricsheet does not supply delivery timestamps. The primary weather model therefore uses the hourly value nearest the scheduled local start. A start-to-plus-60-minute mean is a sensitivity analysis and must be described as an approximation to early-match conditions. Full-day weather can be stored and graphed but cannot be a predictor.

For second innings, the first-innings total and target are technically known by over 10, but the primary model excludes them so first- and second-innings rows answer a comparable question. A chasing-only sensitivity model may include the pre-innings target if it is declared in advance.

## 7. Pitch data and coding

Use only reports demonstrably published before the match began. Record the URL, title, publication/access times, coder, confidence, original match identifiers, a short paraphrase, and coded features.

The pitch representation has two layers:

1. a mutually exclusive primary category for summaries; and
2. multidimensional ordinal/binary features for models.

At least 20% of reports should be independently coded twice. Report raw agreement and weighted Cohen's kappa for ordinal dimensions. Resolve disagreements without inspecting match outcomes.

## 8. Weather construction

1. Manually validate each venue's latitude, longitude, IANA timezone, and canonical name.
2. Request all hourly variables for the local match date and save the unmodified JSON response.
3. Join scheduled start time from a cited pre-match schedule source.
4. Select the nearest hourly observation to scheduled start for the primary model.
5. Preserve temperature, humidity, precipitation, cloud cover, wind speed, and dew point as continuous variables.
6. Keep precipitation zero-inflated as continuous; consider `log1p(precipitation)` only as a prespecified sensitivity transform.

Open-Meteo historical data are reanalysis/model estimates, not exact measurements at the pitch. State that limitation.

## 9. Team and opponent strength

Primary measure: pre-match Elo rating.

- Start teams at 1500.
- Assign focal and opponent ratings before each match update.
- Batch matches played on the same date: assign all ratings first, then apply that date's updates. This prevents an unknown same-day ordering from leaking one match into another.
- Save `team_elo_pre`, `opponent_elo_pre`, and `elo_difference`.

Sensitivity measure: rolling win rate over the prior 20 decided ODIs, again excluding the focal date and future matches. Do not use a ranking downloaded after the study period.

## 10. Feature sets

### Primary score-and-wickets model

- `pp_runs`
- `pp_wickets`
- pitch variables
- start-hour weather variables
- `elo_difference`
- batting first/chasing
- toss winner and decision
- venue or a defensible venue grouping
- year

Do **not** include `pp_run_rate` alongside `pp_runs` in complete 10-over rows; they are deterministic multiples. Keep run rate for description and use it only in an alternative specification.

### Secondary scoring-process model

Use wickets, boundary percentage, and dot-ball percentage without powerplay runs/run rate. This asks whether *how* a start was produced carries information.

### Interactions

Primary confirmatory interactions:

- runs × pitch primary category;
- wickets × pitch primary category;
- runs × innings order;
- wickets × innings order.

Limit weather interactions to a small, prespecified set such as runs × humidity and wickets × precipitation. Standardize continuous variables using training-fold statistics before interactions. Plot marginal predictions rather than interpreting interaction coefficients alone.

## 11. Models

### Baselines

1. prevalence/intercept-only probability;
2. logistic regression with runs and wickets only;
3. logistic regression with runs, wickets, and context but no pitch/weather interactions.

### Interpretable model

Penalized logistic regression is the primary model. Report odds ratios and uncertainty, but use marginal win-probability plots for accessible interpretation. Check whether runs need a spline or quadratic term; decide using training data only.

### Nonlinear models

- Random Forest with constrained depth/leaf size.
- XGBoost with shallow trees, learning-rate regularization, and early stopping inside chronological training folds.

Nonlinear models are challengers, not automatically superior. Hyperparameters are chosen without touching the locked test set.

## 12. Chronological validation

Never make a random row split.

### Pilot outer split

- Development: 2015 and 2019.
- Locked final test: 2023.

### Inner tuning

Use rolling origin, for example earlier matches to validate on later matches within the development period. If exact time ordering is only daily, keep same-day matches together. Fit imputers, scalers, encoders, interaction construction, and feature selection inside each training fold.

## 13. Evaluation and uncertainty

Report with 95% match-clustered bootstrap confidence intervals:

- accuracy at a prespecified 0.50 threshold;
- ROC-AUC;
- log loss;
- Brier score;
- calibration intercept and slope;
- calibration curve with uncertainty bands.

Compare against the prevalence baseline and simple runs+wickets baseline. Accuracy alone is insufficient. Store one prediction row per model/team-innings with match ID, split, observed label, and predicted probability.

## 14. Interpretation and graphics

Required figures:

1. cohort flow diagram;
2. distributions of runs/wickets by year, innings order, and pitch category;
3. observed win rate with binomial intervals across sensible run/wicket bins (descriptive only);
4. logistic marginal win-probability surfaces across runs, wickets, and selected conditions;
5. calibration curves for every final model;
6. permutation importance for nonlinear models;
7. SHAP summary and dependence plots for the locked test set;
8. model comparison with confidence intervals.

SHAP explains the fitted model, not causal effects. Prefer held-out permutation importance as the main global nonlinear importance measure.

## 15. Robustness and sensitivity analyses

- Complete-case versus explicit missing/unknown categories.
- Primary pitch coding versus multidimensional coding.
- Runs versus run rate alternative specification.
- Team-innings versus paired match dataset.
- World Cup pilot versus broader ODI sample.
- Excluding neutral venues or separating host advantage.
- Adding DLS/revised matches only in a documented sensitivity cohort.
- Weather at scheduled start versus start-to-plus-60-minute mean.
- Elo versus rolling prior-20 win rate.

## 16. Minimum reporting standard

Report cohort counts, class balance, missingness, unmatched joins, source coverage, inter-coder reliability, exclusions, feature correlations, chronological split dates, all model settings, confidence intervals, calibration, and limitations. Publish code and non-restricted derived data where licences allow; otherwise publish data-building instructions and checksums.

