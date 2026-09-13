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

## Legacy 228-code re-audit gate: completed

The first 228 tracked pitch codes were produced under an earlier codebook. Their
source URLs and timing evidence remain useful, but their analytical fields were
reviewed again against the current explicit-source-only rule. The 15 batch-24
rows were already coded under that rule.

The completed re-audit:

1. re-opened the eligible pre-match evidence for every legacy row;
2. retained only playing effects explicitly stated by the source;
3. blanked values supported only by physical descriptors or analyst cricket knowledge;
4. recorded each disposition in `data/manual/pitch_code_reaudit.csv`; and
5. materialized the reduced compliant release without source-unavailable rows.

The registry contains 228 reviewed legacy rows: 169 `passed_revised`, 45
`passed_unchanged`, and 14 `source_unavailable`, plus 15
`current_standard` rows. It has zero validation issues. The 229-row compliant
release therefore contains 214 accepted legacy rows and all 15 current-standard
rows; the 14 source-unavailable rows are excluded rather than assigned codes.

Run `.venv/bin/python scripts/audit_pitch_reaudit.py` to reproduce the registry
audit. Run `.venv/bin/python scripts/build_compliant_pitch_release.py` to
materialize `data/processed/pitch_reports_compliant.csv` and
`artifacts/tables/pitch_compliant_release.json`. The compliant model table is
built from that release, never from the mixed-status manual input.

Independent 20% double-coding remains a separate human reliability gate. Until
that gate passes, pitch-effect estimates remain prespecified/reproducible
analysis outputs rather than a final reliability-cleared claim.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
| Matches reviewed in twenty-four 25-match batches | 600 |
| Timing-verified pre-match reports | 243 |
| Reviewed matches set aside | 357 |
| Unreviewed matches | 494 |
| Compliant pitch release | 229 |
| Compliant pitch model-table merge | 229 |
| Source/timing coverage | 22.212066% |


The tracked `data/manual/pitch_reports_verified.csv` and
`data/manual/match_start_times_verified.csv` files contain the 243
source/timing-verified rows used as the auditable input release. They retain
source provenance, source-publication time, collection time (`accessed_at_utc`),
original codes, and short original paraphrases—not copied article text.
`data/processed/pitch_reports_compliant.csv` is the strict 229-row analytical
release after re-audit. `data/manual/pitch_set_aside.csv` records the 357 reviewed
matches without currently eligible analysis. `artifacts/tables/pitch_collection_status.csv`
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
the two innings are paired observations, not independent games. The 229-row
compliant release exceeds that source- and timing-verified target after 14
source-unavailable rows were excluded. Its final analytical use remains subject
to missingness, source selection, and the independent coding reliability gate.

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
and article availability remain measurement and selection risks; independent
double-coding remains the required reliability gate after the completed
explicit-source-only re-audit.

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
`data/manual/pitch_reliability_sample_template.csv` currently contains 46 rows
from the 229-row compliant reference set, spans all represented years and
competition types, retains the same eligible pre-match source documents and match
identity, and blanks every first-coder pitch judgment.

The second coder must follow the same explicit-source-only rule: standardize only
playing effects stated by the source and never infer an effect from physical pitch
wording or cricket knowledge. The reproduction pipeline passes
`data/processed/pitch_reports_compliant.csv` explicitly so the assignment cannot
silently revert to the 243-row mixed-status input.

The reliability audit reports comparable item counts and raw agreement. Cohen's
kappa is linearly weighted for the three ordinal support/ease fields and unweighted
otherwise. Blank optional codes are excluded from that field's agreement denominator
rather than counted as agreements; field completion remains explicit.
