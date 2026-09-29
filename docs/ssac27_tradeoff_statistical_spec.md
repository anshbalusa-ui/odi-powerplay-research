# SSAC27 run–wicket trade-off statistical specification

## Status and claim boundary

This document specifies the primary observational analysis of ODI powerplay run–wicket exchange rates. It is an implementable analysis specification, not a claim that the analysis has been newly preregistered: preliminary modeling using 2015–2024 outcomes has already occurred. Any later analysis must disclose that history and be described as a prespecified specification adopted after preliminary modeling, not as fully preregistered or outcome-blind. No numerical finding is asserted here. The 2025+ locked period remains untouched and is not part of this specification's fitting, tuning, reference-state selection, support determination, or interpretation.

The target is the probability that a batting team wins, conditional on its observed powerplay and pre-match context:

\[
P(Y_{ij}=1\mid R_{ij},W_{ij},C_{ij}),
\]

where \(i\) indexes matches, \(j\in\{1,2\}\) indexes the batting team's innings, \(Y\) is `batting_team_won`, \(R\) is `pp_runs`, \(W\) is `pp_wickets` (wickets lost), and \(C\) contains only the listed context variables. This is a team-innings conditional association/prediction, not a causal effect of intervening on runs or wickets. Inference is clustered by match. It does not describe the chance of a match result twice independently.

## Cohort, rows, and splits

For this amended-source SSAC27 analysis use exactly the 942 frozen-registry, clean men's ODIs dated 2015–2024 from the SHA-identified September 29 Cricsheet archive (871 development matches through 2023; 71 temporal validation matches in 2024). The original fixed September 10 archive is unavailable, so this does **not** reproduce the historical 1,094-match 2015–2026 release, whose other 152 registry IDs are locked 2025+ metadata only. Keep exactly two team-innings per match and exclude undecided or incomplete matches under existing cohort rules rather than inventing labels. Preserve both innings in the same partition and resample. Do not open 2025+ outcome records.

Fit the primary model on development rows only. Use expanding rolling-origin folds wholly within development for any training-only choices (including the specified spline decision, if invoked); group same-date matches together. Freeze the selected specification and preprocessing before predicting the 2024 rows. Do not refit or recalibrate using 2024 outcomes. The locked period is not evaluated under this task.

## Primary probability model and predictor coding

The primary estimator is one pooled, penalized logistic regression on team-innings rows:

\[
\operatorname{logit}(p_{ij})=\eta_{ij}=\beta_0+f_R(R_{ij})+f_W(W_{ij})+\boldsymbol\gamma^T C_{ij}+\boldsymbol\theta^T I_{ij}.
\]

Here \(I\) contains only the interactions listed below. Main effects for every interaction operand are included. Use L2-penalized logistic regression with the current implementation's `C=1.0`, `liblinear` solver, and `max_iter=2000`; retain that fixed setting rather than tune it on 2024. Fit median imputation, missingness indicators for numeric fields, scaling, and categorical encoding on the training fold only, following the existing modeling pipeline. Use unknown-category handling at prediction time. No outcome, post-match, or locked-period information may enter predictors or preprocessing.

- Powerplay performance: `pp_runs` and `pp_wickets`; do not include deterministic `pp_run_rate` alongside runs. The linear term in runs is primary. A restricted cubic spline for runs with three interior knots at development-only 10th, 50th, and 90th percentiles is a single prespecified functional-form sensitivity, not a model search; use the linear model as primary regardless of sensitivity performance. If a knot is non-distinct or the spline design is rank-deficient, do not fit that sensitivity and report it as undefined.
- Innings context: `batting_first` (1 first innings, 0 chase), `batting_team_won_toss`, and `toss_decision`.
- Pre-match strength: `elo_difference` from the batting team's perspective, plus the existing `team_prior_matches`, `opponent_prior_matches`, `team_prior20_win_rate`, and `opponent_prior20_win_rate` features. Elo uses ratings assigned before each match and updates batched by date; rolling rates use only prior decided matches and exclude the focal date. Do not substitute end-of-period rankings.
- Context: `venue`, `rule_era`, `competition_type`, and `year`, using the existing definitions. Venue category levels and numeric preprocessing are learned on development data only. A venue not seen during fit maps to the encoder's all-zero unknown representation; it is not assigned an invented venue effect.
- Prior venue environment: the leakage-safe, exact-name prior-20-match history only, represented by `venue_history_available`, `venue_prior_matches`, `venue_prior_pp_runs_mean`, and `venue_prior_pp_wickets_mean`. These summarize strictly earlier-date matches, with same-date matches batched; they are not measurements of the focal prepared pitch. Where unavailable, preserve missingness (plus the existing availability variable and training-fitted numeric imputation); do not backfill with focal-match data. Venue-history features enter only in the dedicated interaction/venue-history extension described below, not as a second pitch measure.

Use the development-fitted transformations for all estimates. Center and scale continuous interaction operands using development-fold means and standard deviations; compute products from these transformed operands. This reduces arbitrary numerical conditioning but does not change the estimand. If an operand has zero development variance or a product is aliased with existing columns, drop that interaction under the hierarchy below and record it before validation predictions.

## Prespecified interaction hierarchy and parsimony

First fit the primary additive model above. Next fit a single predeclared interaction extension containing both run and wicket interactions with innings order and batting-team pre-match strength:

1. runs × `batting_first`;
2. wickets × `batting_first`;
3. runs × `elo_difference`;
4. wickets × `elo_difference`.

Then add the prespecified prior venue scoring-environment interactions:

5. runs × `venue_prior_pp_runs_mean`;
6. wickets × `venue_prior_pp_runs_mean`.

Use this same development-only prior venue scoring operand for both run and wicket slopes; it is the prior mean powerplay runs per innings, not a focal-pitch measure. This six-term model is the primary context-heterogeneity model. The additive model remains the prespecified benchmark and primary reference for overall average conditional associations; the six-term model is primary for the specified context-dependent exchange-rate estimand. The four-term innings/strength model without venue interactions is a prespecified intermediate sensitivity. Fit the six-term primary model only if development-only support/rank checks pass; otherwise report unsupported terms and the affected estimand as undefined rather than silently changing the primary interaction specification. Do not add all pairwise combinations, interactions with every strength proxy, or data-selected interactions. Do not choose between these fixed models by 2024 performance.

Because run and run rate are deterministically collinear, never enter both. Do not simultaneously use Elo difference and rating-derived duplicate strength representations such as Elo of each side plus their difference. Existing rolling win-rate covariates may remain as distinct historical form measures but are not extra interaction operands. For categorical venue, use one reference level learned from development only and L2 shrinkage; do not include a complete set of indicators plus an intercept. Numerical rank/alias checks and hierarchy-respecting term removal occur on development rows only. Do not use stepwise p-value selection. With two innings per match, do not use match fixed effects or conditional logistic regression: conditioning on each match's complementary win/loss pair removes the match intercept and does not provide the requested absolute calibrated probability. Use pooled marginal logistic probability estimates and match-clustered uncertainty instead.

## Run–wicket exchange-rate estimand

The primary exchange-rate estimand is the additional powerplay runs associated with one additional wicket lost, holding the specified pre-match context and innings state fixed, that yields the same model-predicted win probability. For a valid reference context \(C^*\), innings state \(B^*\), baseline wicket count \(w\), and run count \(r\), define \(\Delta(r,w,C^*,B^*)\) as the nonnegative solution to

\[
\hat p(r+\Delta,w+1,C^*,B^*)=\hat p(r,w,C^*,B^*),\quad
\hat p=\operatorname{logit}^{-1}(\hat\eta).
\]

Thus the reportable exchange rate is runs per additional wicket lost (not wickets per run). It is a model-standardized conditional contrast, not an estimate that runs can causally compensate a wicket. Calculate it from the fitted model including all prespecified terms for the relevant analysis; do not derive it from a single coefficient ratio when interactions are present. For the linear additive logit special case it reduces to \(-\beta_W/\beta_R\) if \(\beta_R>0\), but the numerical root definition governs reporting.

### Reference contexts and common support

Set all reference values using development data only, without inspecting 2024 outcomes:

- Evaluate both innings states, `batting_first=1` and chase (`batting_first=0`).
- Define strength contexts as batting-team `elo_difference` equal to the development median minus one development standard deviation, the development median, and the development median plus one development standard deviation. Define venue contexts as `venue_prior_pp_runs_mean` at its development 25th percentile, median, and 75th percentile among rows with venue history available; set history availability to 1. Cross these strength and venue states with both innings states (up to 18 contexts). Use the same venue context operand for run and wicket interactions.
- Set remaining categorical context to the development modal category/state, ties lexicographically; set other continuous non-focal covariates to development medians. Record all fixed values. A categorical level absent from the relevant development fit makes that context undefined.
- The primary exchange-rate contrast is 1→2 wickets at starting runs equal to the overall development median `pp_runs`, rounded to nearest integer, half upward. Sensitivity contrasts are 0→1 and 2→3 wickets at that same starting-run reference. Do not average over wicket states. Report the primary 1→2 result first; report the two other transitions only as labeled sensitivities.
- Use a fixed development-only, wicket-stratified local support rule rather than a convex hull over pooled wicket counts. For each requested innings × wicket-state × Elo × venue context, select development rows with the exact innings and wicket count; nuisance categorical controls are not required to match exactly. Require each fixed categorical level (including venue, rule era, competition type, toss decision, and toss-winner state) to occur in development; prediction controls remain at the development modal categories specified above. Require venue history available for the interaction model. Standardize `elo_difference` and `venue_prior_pp_runs_mean` by their development means and standard deviations, and define the local neighborhood as rows within one development SD of the requested value on each of those two dimensions. Require at least 20 distinct match IDs in that neighborhood; otherwise the context/state is unsupported. For each supported neighborhood, define the run envelope as the 5th–95th percentiles of `pp_runs` among its rows. Require the baseline run value and every run on the candidate root path to lie within that envelope for the relevant wicket state. Apply the rule separately to the starting and ending wicket states, so no convex-hull interpolation across integer wicket strata can establish support. For an additive benchmark without venue history, omit venue distance and require at least 20 distinct matches within one development SD of Elo, exact innings/wicket state, with its own run envelope. All cutoffs and neighborhood counts use development predictors only; if any reference context or point on its run path fails these checks, report it undefined for unsupported local joint support. The 20-match floor is prespecified and is not reduced when a cell fails.

The prespecified displayed grid is innings (first/chase) × three Elo states × three venue-history states, for the primary 1→2 contrast, plus 0→1 and 2→3 sensitivities where supported. Report each grid cell and its support/undefined reason; do not compute an equally weighted grand mean across states as the headline.

### Bounded numerical root and undefined cases

Use a deterministic bracketed root solver (bisection) on \(g(\delta)=\hat p(r+\delta,w+1,C^*,B^*)-\hat p(r,w,C^*,B^*)\). The lower endpoint is 0; the upper endpoint is the largest nonnegative change for which the entire candidate path remains within the wicket-\(w+1\) local run envelope and has passed the corresponding starting-state support check. Because the run envelope is fixed from development data, this bound is the upper envelope endpoint minus \(r\), when positive. Require the baseline \(r\) and entire candidate interval to satisfy the support rules above. A root is reportable only when the endpoint function values bracket zero (including an endpoint equality); terminate when the interval is at most 0.01 runs or 100 iterations, whichever comes first, and report the midpoint plus bracket width. Since logistic probabilities are monotone in the linear predictor but interaction models can give a local run slope that is zero or negative, do not assume a root exists. If there is no bracketed root, no positive additional-run solution, unsupported baseline/candidate, invalid reference, or numerical nonconvergence, report `undefined` with a controlled reason; never extrapolate, clip an out-of-support answer, or substitute an arbitrary cap. The fixed 0.01-run tolerance is numerical precision, not empirical precision.

## Probability contrasts

Alongside exchange rates, report the predicted probability and probability difference across a fixed development-supported contrast: evaluate all integer run values within the common supported range for a given \(w\), innings, and reference \(C^*\), then display the estimated probabilities and their difference between the supported range endpoints. Derive endpoints from development ranges under the same common-support rule and list them. These curves visualize the conditional model only. No test statistic is inferred from plotted overlap.

## Validation, calibration, and uncertainty

Use the frozen development fit to generate one probability per validation team-innings row. Report validation ROC AUC, log loss, Brier score, and accuracy at 0.50, with identical eligible rows for all model comparisons; include model-wise row and match counts. Report calibration intercept and slope from the validation regression \(Y\sim\alpha+\beta\operatorname{logit}(\hat p)\), with probability clipping only for finite logit evaluation at the evaluation implementation's \(10^{-15}\) boundary. An undefined, nonconvergent, or non-identifiable calibration statistic is explicitly `undefined`, not zero. Show a fixed-width 10-bin reliability table/curve (bins fixed on [0,1], not chosen from validation outcomes), observed rate against mean predicted probability, and bin counts. Empty bins are omitted, not filled.

Use separate bootstrap targets rather than conflating model-fit and validation-sample uncertainty. For validation metrics, calibration coefficients, and fixed-bin calibration-curve points, use 2,000 deterministic percentile bootstrap replicates (seed `20250905`) of the 2024 validation match IDs, retaining both innings rows for each sampled match and using the frozen development-fit probabilities. A duplicated sampled match contributes twice. Compute each replicate's statistic on its resampled validation rows; do not resample individual innings. For calibration bins, keep the fixed bin boundaries; a replicate with no rows in a given bin contributes no estimate for that bin, and report valid replicate count. For probability contrasts and exchange-rate summaries, use 2,000 match-cluster bootstrap replicates of development matches, refit the full model and preprocessing in each replicate, and recompute estimates at reference contexts fixed from the full development sample. Precompute and freeze the local support neighborhoods/envelopes from full development before bootstrapping; do not reconstruct support or select contexts in each replicate. This quantifies fit-sample uncertainty conditional on the prespecified reference states and support. A failed fit or undefined/non-bracketed root is a failed replicate for that statistic; report requested, valid, and failed replicate counts plus counts by undefined-root reason. Use percentile 2.5th/97.5th bounds over valid replicates only and do not suppress failures; if a statistic has no valid bootstrap values, report point estimate if defined and interval undefined with the failure reason. Do not interpret a bootstrap interval as correcting confounding or the outcome-dependent row pairing.

2024 is temporal validation, not training/tuning data. Do not pick interactions, knots, reference states, thresholds, or models because they score better on 2024. The 2024 result estimates transfer to this later period for each frozen specification and is not a locked final test. Compare the additive benchmark, the four-term interaction sensitivity, and the six-term context-heterogeneity primary model as fixed comparisons; never select a winner based on 2024. Calibration is assessed on validation predictions; do not recalibrate the model using validation labels.

## Prespecified sensitivities and reporting

1. **Strength construction:** replace Elo-based strength adjustment with the existing prior-20 win-rate strength features (both batting team and opponent, computed strictly before focal date), retaining all non-strength terms. This is a separate specification; do not include duplicate strength blocks together for this contrast.
2. **Prior venue history:** compare the additive benchmark and four-term innings/strength interaction model with the six-term primary model using both run and wicket interactions with the same prior mean venue powerplay runs; show missing-history counts and distinguish unavailable history from a zero historical average.
3. **Functional form:** the single development-knot restricted cubic spline in runs versus the primary linear run term, with identical cohort and other terms. Do not use a run-rate substitute alongside runs.
4. **Pairing check:** provide a descriptive paired-match formulation by presenting each match's two team-innings probabilities and outcomes together; do not treat the rows as independent or fit match fixed effects for absolute probabilities.
5. **Complete context:** compare the primary training-fitted imputation/missingness-indicator pipeline with complete cases, with counts and both-innings/match exclusions stated; complete-case analysis is sensitivity only.

For each model/specification, report cohort and split counts, class balance, missingness, exclusions, fitted settings, coefficient/term definitions, support/rank decisions, validation metrics, calibration, match-clustered intervals, and deviations from this specification. Present associations, not causes. Label pitch expectations separately from venue scoring history; do not enter historical source-stated pitch codes, new pitch expectations, source prose, or any 2025+ outcome into this primary full-cohort trade-off analysis. Distinguish the verified amended-source 942-match release from the unreproduced original fixed-snapshot claim.
