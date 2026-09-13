# Pitch-Report Collection Status

Last updated: 2026-09-13

The current primary cohort contains 1,094 men's ODIs (2,188 team-innings) from
2015 through the checksummed Cricsheet snapshot. `build_pitch_collection_queue.py`
creates one deterministic, outcome-blind source row per match. Twenty-three
25-match batches have now been reviewed: 228 non-ESPN reports passed source,
timing, and coding validation, while 347 reviewed matches were set aside with
explicit reasons. The prespecified 200-match collection target is exceeded.

## Measurement rule

The collection produces **standardized source-stated pre-match pitch effects**, not independent researcher pitch analysis.

- Code only an expected playing effect explicitly stated by an eligible pre-match source.
- Do not infer spin from dry/dusty/cracked wording.
- Do not infer pace/seam from grass/green/moist wording.
- Do not infer batting ease from hard/flat wording.
- Do not infer slow/two-paced behavior from used/worn/tacky wording.
- Physical descriptions may remain in `short_paraphrased_note` for provenance only.
- If the source does not state the playing effect, leave that effect blank or `unknown`.

This rule applies to first-pass coding, independent recoding, reliability analysis, and every model table built from these reports.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
| Matches reviewed in twenty-three 25-match batches | 575 |
| Timing-verified, source-coded matches | 228 |
| Reviewed matches set aside | 347 |
| Unreviewed matches | 519 |
| Leakage-safe model-table merge | 228 |
| Current cohort coverage | 20.840951% |

The tracked `data/manual/pitch_reports_verified.csv` and
`data/manual/match_start_times_verified.csv` files contain the 228 verified rows.
They contain source provenance, source-publication time, collection time
(`accessed_at_utc`), standardized source-stated effect codes, and short original paraphrases—not copied
article text. `data/manual/pitch_set_aside.csv` records the 347 reviewed matches
without currently eligible analysis. `artifacts/tables/pitch_collection_status.csv`
records all 1,094 cohort matches as 228 `verified`, 347 `set_aside`, or 519
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
the two innings are paired observations, not independent games. The 228-match
released subset exceeds that source- and timing-verified target. This supports an
exploratory, parsimonious analysis of source-stated pre-match pitch effects, but category strata,
missingness, source selection, and independent coding reliability still govern
whether any result is defensible.

## Match-start verification gate

`scripts/build_match_start_queue.py` generates
`data/manual/match_start_times_template.csv` from primary-cohort metadata without
reading result or powerplay fields. The full template has 1,094 pending rows. The
tracked `data/manual/match_start_times_verified.csv` release contains only the 228
rows corresponding to currently verified non-ESPN pitch reports.

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

The 228 reports span 35 normalized provider hostnames. MyKhel contributes 53
matches (23.2%), ICC 36 (15.8%), and Business Standard 26 (11.4%). The top three
providers account for 50.4% of accepted reports; the provider
Herfindahl–Hirschman Index is 1,132 on the conventional 0–10,000 scale.
`scripts/audit_pitch_sources.py` reproduces
`artifacts/tables/pitch_source_providers.csv` and
`artifacts/tables/pitch_source_provider_audit.json`, including provider-specific
source-stated category and coder-confidence counts.

This is intentionally a multi-source **reported-expectation measurement layer** attached to a
single-source Cricsheet ball-by-ball outcome dataset. Provider diversity improves
traceability and reduces dependence on one publisher, but it does not make
editorial descriptions exchangeable. Outlet-specific wording, match selection,
and article availability remain measurement and selection risks; the independent
double-coding gate is therefore unchanged.

## Contributor batch workflow

GitHub issue https://github.com/anshbalusa-ui/odi-powerplay-research/issues/3
tracks the human/licensed collection work. The tracked
`data/manual/pitch_batch_001_template.csv` assigns the first 25 outcome-blind
matches. It covers every cohort year from 2015 through 2026 and all seven
competition types while containing no result, winner, or powerplay columns.

Every queue row includes a probable ESPN ID and unfetched legacy match-URL
candidate because Cricsheet documents its IDs as generally—but not always—the
Cricinfo match IDs. The first-batch search located four relevant ESPN preview
candidates, but they remain set aside: ESPN's reviewed terms require human or
licensed collection rather than automated dataset extraction. A permitted reviewer
must compare the actual page's teams, date, event, and venue, then fill
`espn_match_id_verified`, `espn_match_url_verified`, and set
`espn_linkage_status=verified_match`.

Audit the working linkage state without contacting ESPN:

```bash
.venv/bin/python scripts/audit_espn_linkage.py \
  --input data/manual/pitch_collection_queue_template.csv
```

Do not bulk-open the candidate URLs. They are navigation aids, may be stale or
wrong, and do not establish permission to extract ESPN text.

To select a new batch while skipping attempts already marked `0` or `1` in the
ignored `pitch_reports.csv` working file:

```bash
.venv/bin/python scripts/select_pitch_batch.py \
  --newest-first \
  --n 25 \
  --output data/manual/pitch_batch_working.csv
```

Balanced selection first covers unrepresented years, then unrepresented competition
types, then fills year × competition strata in deterministic rounds. Use
`--newest-first` to prioritize recent unreviewed matches while preserving the same
outcome-blind queue. Use a documented seed or output filename for parallel
contributors, and reserve match IDs in issue #3 before starting to avoid duplicate
work.

Copy completed batch rows into the ignored `data/manual/pitch_reports.csv` working
file. Run `audit_pitch_collection.py` with verified UTC match starts before merging,
then export unsupported attempts for later review:

```bash
.venv/bin/python scripts/export_pitch_set_aside.py \
  --pitch-input data/manual/pitch_reports.csv
```

The public verified, set-aside, and collection-status files are minimized releases:
no source passage, score, result, or powerplay metric is copied into them.
Independently double-code at least 46 of the 228 usable rows before treating any
source-stated pitch-effect model as a research result.

## Independent coding reliability gate

`scripts/build_pitch_reliability_sample.py` selects a deterministic 20% assignment
without inspecting outcomes or first-coder values. The tracked
`data/manual/pitch_reliability_sample_template.csv` currently contains 46 rows,
spans all represented years and competition types, retains the same eligible
pre-match source documents and match identity, and blanks every first-coder pitch
judgment. Give this file to a genuinely independent second coder, then store the
completed rows in ignored `data/manual/pitch_reports_double_coded.csv` with a
different `coder_id`.

The second coder must follow the same explicit-source-only rule: standardize only
playing effects stated by the source and never infer an effect from physical pitch
wording or cricket knowledge.

Regenerate the blinded assignment and then audit completed independent codes:

```bash
.venv/bin/python scripts/build_pitch_reliability_sample.py
```

After both files pass source and timestamp validation, run:

```bash
.venv/bin/python scripts/audit_pitch_reliability.py \
  --reference-input data/manual/pitch_reports.csv \
  --recoded-input data/manual/pitch_reports_double_coded.csv \
  --match-start-input data/manual/match_start_times.csv
```

The audit refuses rows outside the primary cohort, sources published at or after
match start, unsupported codes, duplicate match IDs, and same-coder pairs. It
reports comparable item counts and raw agreement. Cohen's kappa is linearly
weighted for the three ordinal support/ease fields and unweighted otherwise. Blank
optional codes are excluded from that field's agreement denominator rather than
counted as agreements; field completion remains explicit.
The command exits nonzero until at least 20% of verified reference matches have
independent paired codes.
