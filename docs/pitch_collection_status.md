# Pitch Collection Status

Last updated: 2026-09-11

The current primary cohort contains 1,094 men's ODIs (2,188 team-innings) from
2015 through the checksummed Cricsheet snapshot. `build_pitch_collection_queue.py`
now creates one deterministic, outcome-blind source row per match. The tracked queue
contains identifiers, date, competition type, venue, teams, and a search query, but
no result or powerplay fields.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
| Scheduled-start rows queued | 1,094 |
| Human-verified scheduled starts | 0 |
| Source rows present in this clone | 0 |
| Timing-verified pitch codes | 0 |
| Current reproducible coverage | 0% |

Earlier project notes reported 16 local working rows and 9 usable provisional codes.
Those source-derived rows were intentionally Git-ignored pending a rights review and
are not present in this clone, so they cannot be audited or counted as current data.
Recover them from the original authorized working copy before collecting duplicates.

## Collection constraint

ESPNcricinfo's reviewed terms prohibit automated extraction for dataset building.
Ball-by-ball commentary and live/post-match pages are also post-start information and
cannot be used as pitch predictors. A human or licensed workflow must collect only
eligible match-specific pre-match reports, record publication and match-start times,
retain short original paraphrases rather than article text, and mark unsupported
matches explicitly.

## Match-start verification gate

`scripts/build_match_start_queue.py` generates
`data/manual/match_start_times_template.csv` from primary-cohort metadata without
reading result or powerplay fields. All 1,094 rows initially have
`start_time_status=pending`; zero are represented as verified data.

A human or licensed collector must copy the template to the Git-ignored
`data/manual/match_start_times.csv`, reconcile the teams/date/event/venue against a
cited schedule or match page, and record:

1. the source URL, title, and UTC access timestamp;
2. the scheduled local datetime without an offset;
3. the venue's IANA timezone name, not a fixed guessed offset;
4. the corresponding UTC datetime;
5. `start_time_status=verified` and an anonymized `verifier_id`.

Run the zero-network audit before pitch validation:

```bash
python scripts/audit_match_start_times.py \
  --input data/manual/match_start_times.csv
```

The audit checks all 1,094 cohort identities, ISO timestamps, IANA timezone
existence, local-date agreement, exact local-to-UTC conversion including historical
daylight-saving rules, provenance fields, duplicate IDs, and explicit reasons for
`unavailable` or `rejected` rows. Downstream pitch audits and model-table generation
discard every timestamp not explicitly marked `verified`.

## Contributor batch workflow

GitHub issue https://github.com/anshbalusa-ui/odi-powerplay-research/issues/3
tracks the human/licensed collection work. The tracked
`data/manual/pitch_batch_001_template.csv` assigns the first 25 outcome-blind
matches. It covers every cohort year from 2015 through 2026 and all seven
competition types while containing no result, winner, or powerplay columns.

Every queue row includes a probable ESPN ID and unfetched legacy match-URL
candidate because Cricsheet documents its IDs as generally—but not always—the
Cricinfo match IDs. All 1,094 candidates remain `unverified_candidate`; generation
performed zero ESPN network requests. Before citing any ESPN source, a human or
licensed collector must compare the actual page's teams, date, event, and venue,
then fill `espn_match_id_verified`, `espn_match_url_verified`, and set
`espn_linkage_status=verified_match`.

Audit the working linkage state without contacting ESPN:

```bash
python scripts/audit_espn_linkage.py \
  --input data/manual/pitch_collection_queue_template.csv
```

Do not bulk-open the candidate URLs. They are navigation aids, may be stale or
wrong, and do not establish permission to extract ESPN text.

To select a new batch while skipping attempts already marked `0` or `1` in the
ignored `pitch_reports.csv` working file:

```bash
python scripts/select_pitch_batch.py \
  --n 25 \
  --seed 20250905 \
  --output data/manual/pitch_batch_working.csv
```

Selection first covers unrepresented years, then unrepresented competition types,
then fills year × competition strata in deterministic rounds. Use a different
documented seed or output filename for parallel contributors, and reserve match IDs
in issue #3 before starting to avoid duplicate work.

Copy completed batch rows into the ignored `data/manual/pitch_reports.csv` working
file. Recover any authorized prior rows first. Run `audit_pitch_collection.py` with
verified UTC match starts before merging. Independently double-code at least 20% of
usable rows before fitting any pitch-adjusted model.

## Independent coding reliability gate

Select at least 20% of verified reference rows at random without inspecting their
pitch codes. Give the second coder the same eligible pre-match source documents,
match identity, and coding guide, but do not disclose the first coder's codes,
powerplay metrics, or result. Store the independent rows in the ignored
`data/manual/pitch_reports_double_coded.csv` file with genuinely different
`coder_id` values.

After both files pass source and timestamp validation, run:

```bash
python scripts/audit_pitch_reliability.py \
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
