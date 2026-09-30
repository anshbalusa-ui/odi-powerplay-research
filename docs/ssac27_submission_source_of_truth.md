# SSAC27 submission source of truth — corrected amended-source release

**Working title:** What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket

**Technical question:** Among men's ODIs, how many additional first-ten-over runs are associated with the same modeled match win probability as losing one additional wicket, and how does that run-wicket exchange rate vary with innings order, pre-match team strength, and prior venue scoring environment?

**Plain-language question:** What is a powerplay wicket worth in runs, and does that value change with match context?

This page is the current submission narrative and figure/table input sheet, not a new analysis specification. Exact numbers, limitations and provenance are in [`ssac27_numeric_handoff.md`](ssac27_numeric_handoff.md); the frozen estimand and support rules are in [`ssac27_powerplay_tradeoff_protocol.md`](ssac27_powerplay_tradeoff_protocol.md). The ignored local corrected release is `artifacts/ssac27_tradeoff/`, integrity-checked by its 14-file `release_manifest.json` and passing `statistical_qa.json`. The tracked aggregate abstract evidence and ledger in `artifacts/abstract/` are regenerated from that release, not from preliminary model tables. The original September 10 Cricsheet ZIP is unavailable; this analysis uses the official September 29 amended source, **not** a reproduction of the original snapshot.

## Estimand and cohort

For first-ten-over runs $R$, wickets lost $W$, and fixed match context $C$, solve $p(R+d,W+1,C)=p(R,W,C)$ for a **bounded, nonnegative** additional-run amount $d$ within development-data support. The primary contrast is 1→2 wickets at $R=47$; its root is a model-standardized observational association, neither a causal compensation rule nor a universal price. The 18 frozen contexts cross batting first/chasing, pre-match Elo difference −107.473/0/+107.473 and strictly earlier-date prior-venue powerplay mean 43.141/47.908/53.014 runs. Earlier-date venue history describes previous scoring, **not** the focal prepared pitch.

The amended-source unlocked cohort contains **942 clean men's ODI matches, 1,884 paired team-innings (2015–2024)**: **871 matches/1,742 innings** in development through 2023 and **71 matches/142 innings** in untouched 2024 temporal validation. Both innings stay in the same match split or resample. A further 152 registry IDs dated 2025+ were counted from metadata only; **zero 2025+ outcome records opened, trained on or scored**. World Cups are a subgroup. Six-interaction L2 logistic regression is the frozen primary specification; the fixed additive and four-term specifications are comparators, not replacement estimands.

## Supported results and limits

All 18 primary **fixed-run wicket-loss probability contrasts** at 47 runs have development support and match-refit intervals. Only **3/18** primary added-run roots are finite, nonnegative and bracketed within the local second-wicket run envelope. The remaining **15 are undefined, not zero**; never average defined roots into a universal wicket value. The three **individual-root** percentile intervals below condition on refits where that particular bounded root exists:

| Batting innings | Elo difference | Earlier-date venue mean | Additional runs for 1→2 wickets | Conditional 95% interval | Root-valid development refits / 1,000 |
|---|---:|---:|---:|---:|---:|
| First | +107.473 | 47.908 | 14.143 | 4.124–18.450 | 735 |
| First | +107.473 | 53.014 | 13.248 | 4.713–17.481 | 758 |
| Chase | +107.473 | 53.014 | 29.763 | 13.844–30.934 | 563 |

At neutral Elo and median prior-venue scoring, first-innings predicted win probability at 47 runs changes **0.5046→0.3995** from one to two wickets: **−10.505 percentage points**, 95% match-refit interval **−15.473 to −7.215**. For a chase it changes **0.5578→0.4009**, **−15.690 points**, interval **−20.614 to −12.698**. The paired first-minus-chase *wicket-loss probability-difference* contrast is **+5.185 points**, paired interval **−0.457 to +11.182**; this interval includes zero. All **45** predeclared context pairs have fixed-run paired intervals (90 rows including separate root-difference statuses). Only two root differences have both point roots, and **neither has a reportable paired root-difference interval**: 476/1,000 and 703/1,000 jointly valid refits fail the frozen ≥80% gate. The distinct 0→1 sensitivity has six finite roots (13.251–19.571 runs); 2→3 has none. Neither substitutes for the primary 1→2 result.

Untouched 2024 validation, same 71 matches/142 innings:

| Frozen model | ROC AUC (95% match interval) | Log loss | Brier | Accuracy ≥0.50 | Calibration slope |
|---|---:|---:|---:|---:|---:|
| Six-term primary | **0.6626 (0.5461–0.7681)** | 0.6726 | 0.2368 | 0.5986 | 0.536 |
| Additive comparator | 0.6737 (0.5554–0.7764) | 0.6650 | 0.2335 | 0.5986 | 0.568 |
| Four-term comparator | 0.6784 (0.5606–0.7810) | 0.6669 | 0.2334 | 0.6127 | 0.557 |

The primary **did not improve** held-out ROC AUC or log loss against either comparator. Its calibration slope interval is 0.168–1.008; validation has only 71 independent matches. Development uncertainty uses **1,000 requested/1,000 valid** whole-match refits; each model's 2024 validation uncertainty uses **2,000/2,000** whole-match fixed-prediction resamples. Independent statistical QA passes. Previous local testing and CI are recorded in the numerical handoff; recheck fresh branch status before submission.

## Figure 1 and Table 1 inputs (two assets combined)

- **Figure 1:** The already-generated, ignored `artifacts/ssac27_tradeoff/primary_exchange_rates.png` is the corrected, visually inspected figure source; do not publish it as a tracked/public asset before rights review. Its left panel plots **all 18** supported 1→2 fixed-run probability losses at 47 runs with development match-refit intervals, grouped by first/chase × three Elo states × three earlier-date venue states. Its right panel plots **only the three finite supported roots**, with conditional root intervals, and explicitly labels **15 undefined**; it does not print root values or valid-refit counts beside points. Use **Table 1** for the exact 14.143/13.248/29.763 root values, conditional intervals and 735/758/563 valid-refit counts. Conditional individual-root intervals are not paired root-difference intervals. The source values reside in `context_exchange_rates.json` and `paired_context_differences.json` under the ignored release; do not redesign or refit the frozen figure to duplicate Table 1.
- **Table 1:** Use the **three-row finite-root table above**, exactly as labeled: innings, pre-match Elo difference, earlier-date prior-venue powerplay mean, added runs at the supported 1→2 root, its **conditional** individual-root 95% match-refit interval, and valid-root refits out of 1,000. Never substitute the three-model performance table for this asset or report the two unsupported paired root-difference intervals. Label validation comparisons separately in text. Total combined submission assets **at most two**. Both figure and table are submission inputs requiring rights review, not newly published data assets.

## Claim gates and archival boundary

**Allowed:** conditional association and context dependence; supported fixed-run probability contrasts with their uncertainty; three conditional finite roots with their individual-root stability counts; neutral paired probability contrast with interval crossing zero; exact held-out comparator metrics and non-improvement; amended-source, lock and support caveats.

**Prohibited as current SSAC27 claims:** a causal value of sacrificing/preserving a wicket, a single universal rate, treating an undefined root as zero, a paired root-difference CI for either of the two point differences, an improvement over fixed comparators, use of 2025+ outcomes, a fully outcome-blind preregistration claim, or pitch as an SSAC27 primary predictor. Historical preliminary **1,094-match** cohort and **0.740/0.708/0.710** AUC and **+0.082/−0.126** contrast outputs are retained elsewhere **only as superseded historical provenance**; they are not corrected-release abstract results. Earlier source-stated pre-match pitch effects remain a separately re-audited historical derivative. The distinct **model-estimated pre-match expected playing environment** is unapproved for outcome analysis and is neither true pitch measurement nor a finding here. No pitch–outcome association enters the corrected model.
