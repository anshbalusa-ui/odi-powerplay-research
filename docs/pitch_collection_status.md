# Pitch Collection Status

Last updated: 2026-09-09

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

## Next collection step

Copy `data/manual/pitch_collection_queue_template.csv` to the ignored local working
file `data/manual/pitch_reports.csv`. Recover any authorized prior rows, then collect
the next outcome-blind batch. Run `audit_pitch_collection.py` with verified UTC match
starts before merging. Independently double-code at least 20% of usable rows before
fitting any pitch-adjusted model.
