# SSAC27 Submission Checklist

## Competition fields

- **Track:** Other Sports
- **Title:** What Is a Powerplay Wicket Worth? Context-Dependent Run-Wicket Tradeoffs in ODI Cricket
- **Repository:** https://github.com/anshbalusa-ui/odi-powerplay-research
- **Abstract deadline:** October 1, 2026, 11:59 p.m. Eastern Time
- **Figures/tables in abstract:** 0
- **Abstract length:** under 500 words including title and body
- **Required sections:** Introduction, Methods, Results, Conclusion

## Final abstract

Use only:

`docs/ssac27_abstract_skeleton.md`

Do not copy results from older historical sections elsewhere in the repository.

## Current evidence

Before submission, the abstract should remain consistent with:

- `docs/ssac27_submission_source_of_truth.md`
- `docs/ssac27_numeric_handoff.md`
- `artifacts/abstract/ssac27_evidence.json`
- `artifacts/abstract/ssac27_evidence_ledger.csv`
- `artifacts/abstract/ssac27_validation.json`

## Open-source / reproducibility

- Public Cricsheet source is documented.
- Frozen September 29 archive SHA-256 is documented.
- Cohort-selection registry is tracked.
- Locked-safe raw materialization script is tracked.
- 2025+ outcomes remain unopened/unscored.
- Analysis, audit, release, and test commands are documented.
- Data availability/reproduction note: `docs/ssac27_data_availability.md`.

## Claim guardrails

The submission must **not** claim:

- a universal value of a powerplay wicket;
- that undefined roots equal zero;
- a causal benefit from intentionally sacrificing wickets;
- a statistically established innings-order difference from the reported paired interval;
- that the primary model outperforms simpler comparators on 2024 AUC or log loss;
- any pitch-effect result from the current analysis;
- any result using 2025+ outcomes.

## Reviewer path

```text
README
  ↓
final abstract
  ↓
submission source of truth
  ↓
numeric handoff
  ↓
data availability
  ↓
statistical specification + data audit
  ↓
code / tests / aggregate evidence
```

## Final manual portal check

Immediately before submitting:

1. paste the abstract directly from `docs/ssac27_abstract_skeleton.md`;
2. confirm the portal's own word counter is below 500;
3. submit the public repository URL above;
4. select **Other Sports** if the portal asks for a track;
5. confirm no accidental table/figure attachment is included;
6. verify the GitHub repository is public and the README renders correctly.
