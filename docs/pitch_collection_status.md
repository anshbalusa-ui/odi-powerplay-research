# Pitch Collection Status

Last updated: 2026-09-10

The current primary cohort contains 1,094 men's ODIs (2,188 team-innings) from
2015 through the checksummed Cricsheet snapshot. `build_pitch_collection_queue.py`
now creates one deterministic, outcome-blind source row per match. The tracked queue
contains identifiers, date, competition type, venue, teams, and a search query, but
no result or powerplay fields.

## Current reproducible coverage

| Status | Matches |
|---|---:|
| Eligible matches queued | 1,094 |
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

## Contributor batch workflow

GitHub issue https://github.com/anshbalusa-ui/odi-powerplay-research/issues/3
tracks the human/licensed collection work. The tracked
`data/manual/pitch_batch_001_template.csv` assigns the first 25 outcome-blind
matches. It covers every cohort year from 2015 through 2026 and all seven
competition types while containing no result, winner, or powerplay columns.

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
