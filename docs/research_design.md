# Research Design and Analysis Plan

## 1. Study identity

**Working title:** *What Makes a Successful ODI Powerplay? The Role of Aggression, Wicket Preservation, Opposition Strength, and Source-Stated Pitch Effects*

**Design:** retrospective observational prediction/association study with a full-cohort powerplay analysis and a prespecified effect-modification analysis restricted to matches with verified pre-match pitch reports.

**Claim boundary:** the study estimates conditional associations and predictive performance. It does not prove that scoring more quickly causes a win, because team quality, strategy, opposition, and other unmeasured factors influence both powerplay performance and the result.

## 2. Questions and hypotheses

### Primary question

Among men's One Day International cricket matches, how are powerplay aggression and wicket preservation associated with the batting team's probability of winning after accounting for pre-match team strength and match context—and, within the verified-pitch-report subgroup, how do those associations vary by **pitch effects explicitly stated by eligible pre-match sources**?

### Prespecified hypotheses

- **H1:** Conditional on wickets and context, more powerplay runs are associated with higher win probability.
- **H2:** Conditional on runs and context, more powerplay wickets lost are associated with lower win probability.
- **H3:** Within matches with verified pre-match pitch reports, the runs-win and wickets-win relationships vary across **source-stated pitch-effect categories**.
- **H4:** Innings order modifies these relationships because the strategic meaning of a start differs when batting first versus chasing.

H1, H2, and the innings-order component of H4 are tested in the full cohort. H3 is a prespecified subgroup/effect-modification analysis, not a separate unrelated finding and not a reason to discard matches without pitch reports. Bounce and two-paced interactions remain exploratory unless adequate source coverage is established before outcomes are modeled. Testing every possible interaction would create a multiple-comparisons problem.

## 3. Cohort and scope

### Primary cohort

All clean men's ODIs from January 1, 2015 through the fixed Cricsheet data-snapshot date, with no restriction to World Cups or any other event type.

- Include bilateral series, World Cups, Champions Trophies, continental cups, multi-team series, and qualification pathways.
- Label `competition_type` so event mix can be described and used in sensitivity analyses.
- Treat World Cup matches only as a subgroup/generalizability check.
- Use earlier ODIs as a historical sensitivity cohort with explicit era controls rather than silently pooling them into the primary analysis.

### Primary inclusion criteria

- Cricsheet `match_type == "ODI"`.
- Men's matches in the prespecified primary year range; all ODI competition types are eligible.
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
| Pre-match source statements about expected pitch behavior, published before play | Researcher-inferred pitch behavior from dry/grass/moisture/cracks or any post-match pitch summary |
| Toss, batting order, teams, venue, date | Player-of-match, victory margin, final totals |
| Team ratings computed only from earlier dates | End-of-year ranking or tournament-final rating |
| Explicit pre-match dew expectation | Post-match descriptions or observed later-match dew |
| Year and prior history | Statistics calculated using the test/future period |

For second innings, the first-innings total and target are technically known by over 10, but the primary model excludes them so first- and second-innings rows answer a comparable question. A chasing-only sensitivity model may include the pre-innings target if it is declared in advance.

## 7. Pre-match pitch-effect data and coding

Use only reports demonstrably published before the match began. Record the URL, title, publication/access times, coder, confidence, original match identifiers, a short paraphrase, and coded fields.

### Non-inference rule

**The study does not independently analyze or diagnose the pitch.** It standardizes only expected playing effects explicitly stated by the eligible pre-match source.

- A statement that a pitch is dry, dusty, grassy, green, moist, hard, cracked, worn, tacky, or used does not by itself create a model feature.
- `spin_support` is coded only when the source explicitly states or clearly directly describes expected turn/spin assistance.
- `pace_seam_support` is coded only when the source explicitly states or clearly directly describes expected pace/seam/carry/movement assistance.
- `batting_ease` is coded only when the source explicitly states an expected batting/scoring effect.
- `bounce_profile` is coded only when the source explicitly states expected bounce behavior.
- `two_paced_expected` is coded only when the source explicitly states slow/two-paced/holding/stopping or variable-pace behavior.
- If a source contains only a physical surface description and no stated playing effect, preserve the physical description in the provenance paraphrase and leave the corresponding effect blank/`unknown`.

The pitch representation has two analytical layers:

1. a mutually exclusive **source-stated primary behavior category** for summaries; and
2. a lean set of **source-stated model fields**: batting ease, pace/seam support, spin support, bounce profile, and expected two-paced behavior.

Physical surface descriptions may be retained in `short_paraphrased_note` for source transparency, but they are not separate predictors and are never converted into playing-effect fields through cricket knowledge or analyst judgment.
The current auditable input has 243 source/timing-verified rows. The completed
legacy re-audit yields a 229-row compliant derivative after excluding 14
source-unavailable rows; `scripts/build_model_table.py` receives that derivative
explicitly. The independent 20% second-coder sample is generated from the
compliant derivative but has not yet been coded by a genuinely independent human.

At least 20% of reports should be independently coded twice. Report raw agreement and weighted Cohen's kappa for ordinal dimensions. Resolve disagreements without inspecting match outcomes.

## 8. Limited non-pitch conditions

Generic hourly temperature, humidity, precipitation, cloud cover, wind speed, and dew point are excluded from the primary design. They add collection and modeling complexity without directly answering the research question.

`dew_expected` may be retained as a secondary match-condition variable only when an eligible pre-match report explicitly discusses it. Blank means unstated, not no dew. Do not reconstruct later-match dew from a result report or use it as a substitute for a source-stated pitch effect.

## 9. Team and opponent strength

Team strength is a baseline confounding adjustment, not the paper's central explanatory variable. Its purpose is to account for the fact that stronger teams may both produce better powerplays and win more often.

Primary measure: pre-match Elo rating.

- Start teams at 1500.
- Assign focal and opponent ratings before each match update.
- Batch matches played on the same date: assign all ratings first, then apply that date's updates. This prevents an unknown same-day ordering from leaking one match into another.
- Save `team_elo_pre`, `opponent_elo_pre`, and `elo_difference`.

Sensitivity measure: rolling win rate over the prior 20 decided ODIs, again excluding the focal date and future matches. Do not use a ranking downloaded after the study period.

### Historical venue sensitivity

As a source-independent sensitivity analysis, summarize powerplay scoring over the most recent 20 matches at the exact venue name, using only strictly earlier dates. Retain prior-match count and a cold-start indicator. This block may test whether a stable historical scoring environment improves prediction, but it must never be described as the prepared pitch for the focal match or used to backfill missing source-stated pitch codes.

## 10. Feature sets and incremental research design

Fit nested feature blocks so the powerplay contribution is first estimated in the full cohort and then refined in the verified-pitch-report subgroup:

1. **F0 full-cohort pre-match baseline:** Elo difference, prior experience and win rates, toss, innings order, venue, year/rule era, and competition type.
2. **F1 full-cohort powerplay model:** F0 plus `pp_runs` and `pp_wickets`.
3. **F2 full-cohort scoring-process sensitivity:** F0 plus `pp_wickets`, boundary-ball percentage, and dot-ball percentage instead of runs.
4. **V1 venue-history sensitivity:** F1 plus source-independent prior venue-history features and availability.
5. **P0 verified-pitch-report baseline:** F0 restricted to matches with verified reports, plus **source-stated pitch-effect main fields**.
6. **P1 verified-pitch-report powerplay model:** P0 plus `pp_runs` and `pp_wickets`.
7. **P2 verified-pitch-report effect-modification model:** P1 plus the small prespecified interactions with **source-stated pitch effects**.

The primary full-cohort comparison is F0 versus F1/F2. The pitch-report subgroup comparison is P1 versus P2 and asks whether the powerplay relationship changes when pre-match sources explicitly forecast different playing effects. Report subgroup coverage and compare the pitch-report subset with the full cohort before interpreting P2. Never backfill missing source-stated pitch effects with venue history or researcher inference.

### Full-cohort score-and-wickets model

- `pp_runs`
- `pp_wickets`
- `elo_difference`
- batting first/chasing
- toss winner and decision
- venue
- year
- competition type or prespecified competition grouping

Do **not** include `pp_run_rate` alongside `pp_runs` in complete 10-over rows; they are deterministic multiples. Keep run rate for description and use it only in an alternative specification.

### Secondary scoring-process model

Use wickets, boundary percentage, and dot-ball percentage without powerplay runs/run rate. This asks whether *how* a start was produced carries information.

### Interactions

Primary confirmatory interactions in the verified-pitch-report subgroup:

- runs × source-stated batting ease;
- wickets × source-stated batting ease;
- wickets × source-stated pace/seam support;
- wickets × source-stated spin support;
- runs × innings order;
- wickets × innings order.

Treat source-stated bounce and two-paced interactions as exploratory unless their coding coverage is sufficient before outcome modeling. Plot marginal predictions rather than interpreting interaction coefficients alone.

## 11. Models

### Baselines

1. prevalence/intercept-only probability;
2. M0 pre-match/context logistic model without powerplay outcomes;
3. runs-and-wickets-only descriptive benchmark;
4. M1 logistic model with pre-match/context variables plus runs and wickets.

### Interpretable model

Penalized logistic regression is the primary model. Report odds ratios and uncertainty, but use marginal win-probability plots for accessible interpretation. Check whether runs need a spline or quadratic term; decide using training data only.

### Nonlinear models

- Random Forest with constrained depth/leaf size.
- XGBoost with shallow trees, learning-rate regularization, and early stopping inside chronological training folds.

Nonlinear models are challengers, not automatically superior. Hyperparameters are chosen without touching the locked test set.

## 12. Chronological validation

Never make a random row split.

### Primary outer split

- Development and rolling-origin tuning: January 1, 2015 through December 31, 2023.
- Temporal validation: calendar year 2024.
- Locked final test: January 1, 2025 through the fixed 2026 data-snapshot date.

Record the exact snapshot cutoff and row counts before fitting. If a split is too small for stable estimation, revise the date boundaries before examining test outcomes and document the change.

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
2. distributions of runs/wickets by year, innings order, and source-stated pitch-effect category;
3. observed win rate with binomial intervals across sensible run/wicket bins (descriptive only);
4. logistic marginal win-probability surfaces across runs, wickets, and selected source-stated pitch effects;
5. calibration curves for every final model;
6. permutation importance for nonlinear models;
7. SHAP summary and dependence plots for the locked test set;
8. model comparison with confidence intervals.

SHAP explains the fitted model, not causal effects. Prefer held-out permutation importance as the main global nonlinear importance measure.

## 15. Robustness and sensitivity analyses

- Complete-case versus explicit missing/unknown categories.
- Primary source-stated pitch-effect category versus multidimensional source-stated effect fields.
- Runs versus run rate alternative specification.
- Team-innings versus paired match dataset.
- all-modern-ODI primary cohort versus World Cup, competition-type, and historical-era subgroups.
- Excluding neutral venues or separating host advantage.
- Adding DLS/revised matches only in a documented sensitivity cohort.
- models with and without the secondary `dew_expected` variable.
- Elo versus rolling prior-20 win rate.

No robustness analysis may introduce researcher-inferred pitch labels from physical surface descriptions.

## 16. Minimum reporting standard

Report cohort counts, class balance, missingness, unmatched joins, source coverage, inter-coder reliability, exclusions, feature correlations, chronological split dates, all model settings, confidence intervals, calibration, and limitations. State explicitly that pitch variables are standardized source statements, not independent researcher assessments of the surface. Publish code and non-restricted derived data where licences allow; otherwise publish data-building instructions and checksums.
