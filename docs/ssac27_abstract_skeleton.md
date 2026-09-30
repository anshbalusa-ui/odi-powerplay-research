# What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket

## Introduction
How many additional first-ten-over runs are associated with the same modeled match win probability as losing one more wicket? We estimate this run-wicket exchange rate in men's One Day Internationals (ODIs), and assess how it varies with match context.

## Methods
We analyzed 942 clean men's ODI matches (1,884 paired innings) from the amended September 29 Cricsheet source, 2015–2024: 871 development matches (1,742 innings) through 2023 and 71 untouched 2024 validation matches (142 innings). The original September 10 archive was unavailable. The estimand was the nonnegative, bounded run increment $d$ solving $p(R+d,W+1,C)=p(R,W,C)$ at 47 runs and 1→2 wickets. An L2 logistic model with six prespecified interactions estimated win probabilities; context included innings order, pre-match Elo strength, and strictly earlier-date prior venue scoring environment. We reported only supported finite roots, with 1,000 whole-match development refits and 2,000 whole-match validation resamples. Outcomes from 2025 onward were not loaded or scored.

## Results
Only three of 18 supported contexts had finite roots: batting first with strong Elo (+107.473) and median prior venue scoring (47.908), 14.143 runs (95% interval 4.124–18.450; 735/1,000 valid refits); batting first with strong Elo and high venue scoring (53.014), 13.248 (4.713–17.481; 758/1,000); and chasing with strong Elo and high venue scoring, 29.763 (13.844–30.934; 563/1,000). The remaining 15 roots were undefined, not zero. At neutral Elo and median venue scoring, modeled win probability at 47 runs changed from 0.5046 to 0.3995 batting first (−10.505 percentage points; 95% interval −15.473 to −7.215), and from 0.5578 to 0.4009 chasing (−15.690 points; −20.614 to −12.698). Their paired first-minus-chase wicket-loss probability difference was +5.185 points (95% interval −0.457 to +11.182), including zero. Untouched 2024 validation ROC-AUC was 0.6626 (95% match interval 0.5461–0.7681) for the primary, versus 0.6737 additive and 0.6784 four-term; log loss was 0.6726 versus 0.6650 and 0.6669. The primary did not improve AUC or log loss.

## Conclusion
The estimated exchange rate is context-dependent but frequently unsupported: undefined roots cannot be interpreted as zero or as a universal wicket price. These observational estimates describe modeled associations, not causal effects or coaching rules. Pitch measurements were excluded, and no pitch-effect claim is made.
