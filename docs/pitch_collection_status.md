# Pitch Collection Status

Last updated: 2026-09-06

The primary cohort contains 1,093 men's ODIs from 2015 through the fixed Cricsheet snapshot. Pitch collection is performed in outcome-blind, deterministic batches across competition types. Source-derived working rows remain local pending a separate rights review; this document reports only aggregate progress and the prespecified selection method.

## Batch 001 selection

Batch 001 selected 12 matches without reading outcomes or powerplay values. Within each `competition_type`, matches were sorted by date and match ID and selected at evenly spaced quantiles. Quotas were three bilateral-series matches, three qualification-pathway matches, two multi-team-series matches, and one match each from the World Cup, Champions Trophy, continental cup, and other ODI groups.

## Current coverage

| Status | Matches |
|---|---:|
| Previously coded provisional rows | 4 |
| New usable pitch codes from Batch 001 | 5 |
| `source_no_pitch_evidence` | 3 |
| `no_eligible_source` | 4 |
| Total working rows | 16 |
| Usable pitch-coded rows | 9 |

The five new usable rows include two spin/slow-surface expectations, two batting-friendly expectations, and one pace/seam expectation. These counts are collection progress only and are not evidence about match outcomes.

## Next collection step

Repeat the deterministic selection procedure with the next unsearched quantiles, report coverage by year and competition type, and independently double-code a stratified 20% of usable rows before any pitch-adjusted model is fitted.
