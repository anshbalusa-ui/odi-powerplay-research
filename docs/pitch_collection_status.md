# Pitch Collection Status

Last updated: 2026-09-09

The primary cohort contains 1,093 men's ODIs from 2015 through the fixed Cricsheet snapshot. Pitch collection is performed in outcome-blind, deterministic batches across competition types. Source-derived working rows remain local pending a separate rights review; this document reports only aggregate progress and the prespecified selection method.

## Batch selection

Batches 001 and 002 each selected 12 matches without reading outcomes or powerplay values. Within each `competition_type`, unaudited matches were ordered deterministically using match date and a seeded hash of match ID, then sampled at evenly spaced positions. Each batch used quotas of three bilateral-series matches, three qualification-pathway matches, two multi-team-series matches, and one match each from the World Cup, Champions Trophy, continental cup, and other ODI groups.

## Current coverage

| Status | Matches |
|---|---:|
| Usable rows before Batch 002 | 9 |
| New usable pitch codes from Batch 002 | 8 |
| `source_no_pitch_evidence` | 4 |
| `no_eligible_source` | 7 |
| Total working rows | 28 |
| Usable pitch-coded rows | 17 |

Across the 17 usable rows, the primary categories are eight batting-friendly, four spin, two pace/seam, two slow/two-paced, and one balanced. Batch 002 contributed eight usable rows and four explicit missing-evidence rows. These counts are collection progress only and are not evidence about match outcomes.

One same-date source carries a validation warning because the cohort does not yet store an independently comparable UTC match-start time. Its article timestamp is retained rather than silently reducing it to a date. The pitch-adjusted confirmatory model will not run until this timing issue is independently resolved or the row is excluded by the frozen rule.

## Next collection step

Repeat the deterministic selection procedure until the prespecified coverage threshold is met, report coverage by year and competition type, and independently double-code a stratified 20% of usable rows before any pitch-adjusted model is fitted. Rows without eligible evidence remain missing; venue-average descriptions, fantasy prediction pages, toss commentary, and post-match observations are not substituted.
