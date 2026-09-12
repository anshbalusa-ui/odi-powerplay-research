# Pitch Collection Status

Last updated: 2026-09-12

The current primary cohort contains 1,094 men's ODIs (2,188 team-innings) from
2015 through the checksummed Cricsheet snapshot. `build_pitch_collection_queue.py`
creates one deterministic, outcome-blind source row per match. Nineteen 25-match
batches have now been reviewed: 200 non-ESPN reports passed source, timing, and
coding validation, while 275 reviewed matches were set aside with explicit reasons.
The prespecified 200-match collection target is complete.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
| Matches reviewed in nineteen 25-match batches | 475 |
| Timing-verified, source-coded matches | 200 |
| Reviewed matches set aside | 275 |
| Unreviewed matches | 619 |
| Leakage-safe model-table merge | 200 |
| Current cohort coverage | 18.281536% |

The tracked `data/manual/pitch_reports_verified.csv` and
`data/manual/match_start_times_verified.csv` files contain the 200 verified rows.
They contain source provenance, source-publication time, collection time
(`accessed_at_utc`), derived codes, and short original paraphrases—not copied
article text. `data/manual/pitch_set_aside.csv` records the 275 reviewed matches
without currently eligible analysis. `artifacts/tables/pitch_collection_status.csv`
records all 1,094 cohort matches as 200 `verified`, 275 `set_aside`, or 619
`unreviewed`; it contains no outcome or powerplay field.

## Collection constraint

ESPNcricinfo's reviewed terms prohibit automated extraction for dataset building.
Ball-by-ball commentary and live/post-match pages are also post-start information and
cannot be used as pitch predictors. A human or licensed workflow must collect only
eligible match-specific pre-match reports, record publication and match-start times,
retain short original paraphrases rather than article text, and mark unsupported
matches explicitly.

## Prespecified collection target

The usable pitch subset target was 200 matches (400 paired team-innings) from the
modern 2015-forward ODI cohort. The statistical sampling unit remains the match:
the two innings are paired observations, not 400 independent games. The released
subset reaches that source- and timing-verified target. This supports an
exploratory, parsimonious pitch-adjusted analysis, but category strata,
missingness, source selection, and independent coding reliability still govern
whether any result is defensible.

## Match-start verification gate

`scripts/build_match_start_queue.py` generates
`data/manual/match_start_times_template.csv` from primary-cohort metadata without
reading result or powerplay fields. The full template has 1,094 pending rows. The
tracked `data/manual/match_start_times_verified.csv` release contains only the 200
rows corresponding to currently verified non-ESPN pitch reports.

A collector should copy only rows corresponding to collected pitch reports into
the Git-ignored `data/manual/match_start_times.csv`, reconcile the
teams/date/event/venue against a cited schedule or match page, and record:

1. the source URL, title, and UTC access timestamp;
2. the scheduled local datetime without an offset;
3. the venue's IANA timezone name, not a fixed guessed offset;
4. the corresponding UTC datetime;
5. `start_time_status=verified` and an anonymized `verifier_id`.

Run the zero-network audit before pitch validation:

```bash
.venv/bin/python scripts/audit_match_start_times.py \
  --input data/manual/match_start_times_verified.csv
```

The audit checks every provided row's cohort identity, ISO timestamps, IANA
timezone existence, local-date agreement, exact local-to-UTC conversion including
historical daylight-saving rules, provenance fields, duplicate IDs, and explicit
reasons for `unavailable` or `rejected` rows. Use `--require-full-cohort` only to
audit the generated template itself; collectors do not need start times for matches
without pitch reports. Downstream pitch audits and model-table generation discard
every timestamp not explicitly marked `verified`.

## Source-provider audit

The 200 reports span 29 normalized provider hostnames. MyKhel contributes 53
matches (26.5%), ICC 36 (18.0%), and Indian Express 23 (11.5%). The top three
providers account for 56.0% of accepted reports; the provider
Herfindahl–Hirschman Index is 1,313 on the conventional 0–10,000 scale.
`scripts/audit_pitch_sources.py` reproduces
`artifacts/tables/pitch_source_providers.csv` and
`artifacts/tables/pitch_source_provider_audit.json`, including provider-specific
pitch-category and coder-confidence counts.

This is intentionally a multi-source pitch measurement layer attached to a
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
Independently double-code at least 40 of the 200 usable rows before treating any
pitch-adjusted model as a research result.

## Independent coding reliability gate

Select at least 20% of verified reference rows at random without inspecting their
pitch codes. Give the second coder the same eligible pre-match source documents,
match identity, and coding guide, but do not disclose the first coder's codes,
powerplay metrics, or result. Store the independent rows in the ignored
`data/manual/pitch_reports_double_coded.csv` file with genuinely different
`coder_id` values.

After both files pass source and timestamp validation, run:

```bash
.venv/bin/python scripts/audit_pitch_reliability.py \
  --reference-input data/manual/pitch_reports.csv \
  --recoded-input data/manual/pitch_reports_double_coded.csv \
  --match-start-input data/manual/match_start_times.csv
```

The audit refuses rows outside the primary cohort, sources published at or after
match start, unsupported codes, duplicate match IDs, and same-coder pairs. It
reports comparable item counts, raw agreement, and unweighted Cohen's kappa for
each pitch field. Blank optional codes are excluded from that field's agreement
denominator rather than counted as agreements; field completion remains explicit.
The command exits nonzero until at least 20% of verified reference matches have
independent paired codes.
