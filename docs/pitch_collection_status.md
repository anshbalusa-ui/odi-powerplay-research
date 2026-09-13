# Pitch-Report Collection Status

Last updated: 2026-09-13

The current primary cohort contains 1,094 men's ODIs (2,188 team-innings) from
2015 through the checksummed Cricsheet snapshot. `build_pitch_collection_queue.py`
creates one deterministic, outcome-blind source row per match. Twenty-four
25-match batches have now been reviewed: 243 non-ESPN reports passed source and
timing validation, while 357 reviewed matches were set aside with explicit reasons.
The prespecified 200-match source-coverage target is exceeded.

## Measurement rule

The intended analytical layer is **standardized source-stated pre-match pitch effects**, not independent researcher pitch analysis.

- Code only an expected playing effect explicitly stated by an eligible pre-match source.
- Do not infer spin from dry/dusty/cracked wording.
- Do not infer pace/seam from grass/green/moist wording.
- Do not infer batting ease from hard/flat wording.
- Do not infer slow/two-paced behavior from used/worn/tacky wording.
- Physical descriptions may remain in `short_paraphrased_note` for provenance only.
- If the source does not state the playing effect, leave that effect blank or `unknown`.

This rule applies to first-pass coding, independent recoding, reliability analysis, and every model table built from these reports.

## Legacy 228-code re-audit gate

The first 228 currently tracked pitch codes were produced under an earlier
codebook. Their source URLs and timing evidence remain useful, but those analytical
codes are **provisional legacy codes** until re-audited against the current
explicit-source-only rule. The 15 batch-24 rows were coded under the current rule.

Before any final source-stated pitch-effect model or paper claim:

1. revisit each retained eligible pre-match source in the first 228 rows;
2. confirm that every nonblank pitch-effect code is directly supported by an explicit source statement;
3. blank/remove any value based only on physical descriptors or researcher/agent cricket knowledge;
4. record the re-audit status reproducibly;
5. rebuild the pitch-report model table from the compliant rows;
6. then complete the independent 20% double-coding reliability gate using the same strict rule.

Until that re-audit passes, do **not** describe the first 228 analytical codes as
fully source-stated or final. The total source/timing coverage count is 243.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
| Matches reviewed in twenty-four 25-match batches | 600 |
| Timing-verified pre-match reports | 243 |
| Reviewed matches set aside | 357 |
| Unreviewed matches | 494 |
| Current provisional model-table merge | 243 |
| Source/timing coverage | 22.212066% |

The tracked `data/manual/pitch_reports_verified.csv` and
`data/manual/match_start_times_verified.csv` files contain the 243 verified-source/timing rows.
They contain source provenance, source-publication time, collection time
(`accessed_at_utc`), provisional codes, and short original paraphrases—not copied
article text. `data/manual/pitch_set_aside.csv` records the 357 reviewed matches
without currently eligible analysis. `artifacts/tables/pitch_collection_status.csv`
records all 1,094 cohort matches as 243 `verified`, 357 `set_aside`, or 494
`unreviewed`; it contains no outcome or powerplay field.

## Collection constraint

ESPNcricinfo's reviewed terms prohibit automated extraction for dataset building.
Ball-by-ball commentary and live/post-match pages are also post-start information and
cannot be used as pre-match predictors. A human or licensed workflow must collect only
eligible match-specific pre-match reports, record publication and match-start times,
retain short original paraphrases rather than article text, standardize only effects
explicitly stated by the source, and mark unsupported matches explicitly.

## Prespecified collection target

The usable pitch-report subset target was 200 matches (400 paired team-innings) from the
modern 2015-forward ODI cohort. The statistical sampling unit remains the match:
the two innings are paired observations, not independent games. The 243-report
release exceeds that source- and timing-verified target. Whether all 243 remain
analytically usable depends on re-auditing the first 228 rows, category strata,
missingness, source selection, and independent coding reliability.

## Match-start verification gate

`scripts/build_match_start_queue.py` generates
`data/manual/match_start_times_template.csv` from primary-cohort metadata without
reading result or powerplay fields. The full template has 1,094 pending rows. The
tracked `data/manual/match_start_times_verified.csv` release contains only the 243
rows corresponding to currently verified non-ESPN pre-match reports.

A collector should copy only rows corresponding to collected pitch reports into
the Git-ignored `data/manual/match_start_times.csv`, reconcile the
teams/date/event/venue against a cited schedule or match page, and record:

1. the source URL, title, and UTC access timestamp;
2. the scheduled local datetime without an offset;
3. the venue's IANA timezone name, not a fixed guessed offset;
4. the corresponding UTC datetime;
5. `start_time_status=verified` and an anonymized `verifier_id`.

Run the zero-network audit before source-stated pitch-effect validation:

```bash
.venv/bin/python scripts/audit_match_start_times.py \
  --input data/manual/match_start_times_verified.csv
```

The audit checks every provided row's cohort identity, ISO timestamps, IANA
timezone existence, local-date agreement, exact local-to-UTC conversion including
historical daylight-saving rules, provenance fields, duplicate IDs, and explicit
reasons for `unavailable` or `rejected` rows. Use `--require-full-cohort` only to
audit the generated template itself; collectors do not need start times for matches
without pitch reports. Downstream audits and model-table generation discard
every timestamp not explicitly marked `verified`.

## Source-provider audit

The 243 reports span 35 normalized provider hostnames. MyKhel contributes 59
matches (24.3%), ICC 36 (14.8%), and Business Standard 27 (11.1%). The top three
providers account for 50.2% of accepted reports; the provider
Herfindahl–Hirschman Index is 1,131 on the conventional 0–10,000 scale.
`scripts/audit_pitch_sources.py` reproduces
`artifacts/tables/pitch_source_providers.csv` and
`artifacts/tables/pitch_source_provider_audit.json`.

This is intentionally a multi-source reported-expectation measurement layer attached to a
single-source Cricsheet ball-by-ball outcome dataset. Provider diversity improves
traceability and reduces dependence on one publisher, but it does not make
editorial descriptions exchangeable. Outlet-specific wording, match selection,
and article availability remain measurement and selection risks; the explicit-source-only re-audit and independent double-coding gates are therefore required.

## Contributor batch workflow

GitHub issue https://github.com/anshbalusa-ui/odi-powerplay-research/issues/3
tracks the human/licensed collection work. The tracked
`data/manual/pitch_batch_001_template.csv` assigns the first 25 outcome-blind
matches. It covers every cohort year from 2015 through 2026 and all seven
competition types while containing no result, winner, or powerplay columns.

Every queue row includes a probable ESPN ID and unfetched legacy match-URL
candidate because Cricsheet documents its IDs as generally—but not always—the
Cricinfo match IDs. ESPN candidates remain subject to human or licensed collection.
A permitted reviewer must compare the actual page's teams, date, event, and venue,
then fill the verified linkage fields.

Do not bulk-open the candidate URLs. They are navigation aids, may be stale or
wrong, and do not establish permission to extract ESPN text.

For all new coding, use the current codebook immediately. New rows must satisfy the explicit-source-only rule at first pass; they do not get the legacy-code exception.

## Independent coding reliability gate

`scripts/build_pitch_reliability_sample.py` selects a deterministic 20% assignment
without inspecting outcomes or first-coder values. The tracked
`data/manual/pitch_reliability_sample_template.csv` currently contains 49 rows,
spans all represented years and competition types, retains the same eligible
pre-match source documents and match identity, and blanks every first-coder pitch
judgment.

The second coder must follow the same explicit-source-only rule: standardize only
playing effects stated by the source and never infer an effect from physical pitch
wording or cricket knowledge. The reliability sample should be regenerated from the
re-audited compliant reference set if that set changes materially.

The reliability audit reports comparable item counts and raw agreement. Cohen's
kappa is linearly weighted for the three ordinal support/ease fields and unweighted
otherwise. Blank optional codes are excluded from that field's agreement denominator
rather than counted as agreements; field completion remains explicit.
