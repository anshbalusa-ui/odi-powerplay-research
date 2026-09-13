# Data Dictionary

## Dataset levels

| Dataset | Grain | Purpose |
|---|---|---|
| `cricsheet_matches` | one match | stable match metadata and result |
| `powerplay_innings` | one regulation team-innings | first-10-over statistics and context |
| `pitch_reports_verified` | one verified match/source | minimized pre-match provenance plus mixed-status provisional codes: 228 legacy rows pending re-audit and 15 current-rule rows |
| `pitch_set_aside` | one reviewed match | outcome-blind follow-up list for attempts without eligible analysis |
| `pitch_collection_status` | one eligible match | verified source/timing, reviewed set-aside, or unreviewed collection state |
| `pitch_source_providers` | one normalized provider hostname | source share, category mix, and confidence mix for the current provisional release |
| `team_strength_pre` | one match/team | ratings calculated before the match date |
| `venue_conditions_pre_match` | one match | rolling prior-match venue scoring environment |
| `model_team_innings` | one team-innings | audited merged analysis table |
| `model_match_paired` | one match | secondary difference-based analysis table |
| `predictions` | one row/model/team-innings | held-out prediction and label |

## Identifiers and match context

| Variable | Type | Availability | Definition |
|---|---|---|---|
| `match_id` | string | pre-match linkage | Cricsheet JSON filename stem; never infer from row number |
| `match_date` | ISO date | pre-match | first value in `info.dates` |
| `year` | integer | pre-match | calendar year from `match_date` |
| `event_name` | category | pre-match | `info.event.name` when present |
| `competition_type` | category | pre-match | documented broad label: bilateral series, World Cup, Champions Trophy, continental cup, multi-team series, qualification pathway, or other ODI |
| `is_world_cup` | binary | pre-match | 1 only for the main World Cup event; qualifiers and Super League matches remain separate |
| `rule_era` | category | pre-match | prespecified era label; `modern_2015_plus` in the primary cohort |
| `gender` | category | pre-match | Cricsheet match gender |
| `match_type` | category | pre-match | must equal `ODI` in main extractor |
| `venue` | string/category | pre-match | original Cricsheet venue text |
| `venue_canonical` | category | pre-match | manually audited canonical venue |
| `city` | string/category | pre-match | Cricsheet city when present |
| `batting_team` | category | innings start | batting side in the focal innings |
| `opponent` | category | innings start | other team |
| `innings_number` | integer | innings start | regulation innings order, starting at 1 |
| `batting_first` | binary | innings start | 1 for innings 1 |
| `chasing` | binary | innings start | 1 for innings 2 |
| `toss_winner` | category | pre-match | Cricsheet toss winner |
| `toss_decision` | category | pre-match | bat or field |
| `batting_team_won_toss` | binary | pre-match | 1 if focal batting team won toss |

## Outcome fields

These fields may be present in labeled data for training/evaluation but cannot be predictors.

| Variable | Type | Definition |
|---|---|---|
| `match_status` | category | `decided`, `tie`, `no_result`, or `unknown` |
| `winner` | category | eventual winner from Cricsheet |
| `batting_team_won` | binary/nullable | 1 if focal batting side won; null for undecided matches |
| `result_method` | category/nullable | e.g. D/L; used for cohort exclusion/audit, never as a primary predictor |

## First-10-over fields

| Variable | Type | Definition |
|---|---|---|
| `pp_runs` | integer | sum of total runs in over indexes 0–9 |
| `pp_wickets` | integer | wickets lost in indexes 0–9, excluding retired hurt |
| `pp_legal_balls` | integer | deliveries excluding wides and no-balls |
| `pp_delivery_events` | integer | every recorded delivery event, including illegal balls |
| `pp_run_rate` | float | runs × balls per over ÷ legal balls |
| `pp_boundary_balls` | integer | legal batter fours/sixes, excluding `non_boundary` |
| `pp_boundary_pct` | float | 100 × boundary balls ÷ legal balls |
| `pp_dot_balls` | integer | legal deliveries with zero total runs |
| `pp_dot_ball_pct` | float | 100 × dot balls ÷ legal balls |
| `pp_complete` | binary | legal balls ≥ 10 × balls per over |
| `balls_per_over` | integer | Cricsheet expected balls per over |
| `is_super_over` | binary | retained for audit; super-over innings are not emitted |

## Match-start verification fields

`data/manual/match_start_times_template.csv` is outcome-blind and contains one row
per primary-cohort match. `data/manual/match_start_times_verified.csv` is the
tracked, minimized subset supporting the 243 source/timing-verified pre-match
reports. It verifies timing eligibility; it does **not** certify that the first 228
legacy pitch codes already satisfy the current explicit-source-only coding rule.

| Variable | Type | Definition |
|---|---|---|
| `cricsheet_match_id` | string | exact primary-cohort match key |
| `match_date` | ISO date | local scheduled match date copied from the cohort |
| `event_name` | string | event or series identity used for manual reconciliation |
| `competition_type` | category | outcome-blind cohort competition stratum |
| `venue` | string | cohort venue used for identity reconciliation |
| `city` | string | cohort city where available |
| `team_1`, `team_2` | string | teams in innings order; used only to verify identity |
| `source_search_query` | string | unfetched outcome-blind navigation query |
| `source_url` | URL | cited schedule or match page supporting the start time |
| `source_title` | string | title of the cited source |
| `accessed_at_utc` | timestamp | offset-aware ISO-8601 collection timestamp |
| `scheduled_start_local` | local datetime | scheduled local start without a UTC offset |
| `timezone_name` | IANA timezone | location timezone, including historical daylight-saving rules |
| `scheduled_start_utc` | UTC timestamp | local start converted to `Z` or `+00:00` |
| `start_time_status` | category | `pending`, `verified`, `unavailable`, or `rejected` |
| `verifier_id` | string | anonymized verifier label; AI-assisted provisional work is disclosed by its label |
| `verification_note` | string/nullable | concise reconciliation note |
| `exclusion_reason` | string/nullable | required when unavailable or rejected |

The validator requires exact cohort identity, a valid HTTP(S) source, an
offset-aware access timestamp, a real IANA timezone, a local date equal to
`match_date`, and exact timezone conversion to UTC. Only `verified` timestamps are
exposed to pitch-source timing validation. No start-time, timezone, status,
verifier, or source-provenance field is joined to the model table.

The tracked release contains 243 verified scheduled starts.

## Pre-match pitch-report fields

`data/manual/pitch_reports_verified.csv` contains 243 rows that passed source,
publication-time, match-start, cohort-identity, and structural code-value
validation. The first 228 rows were produced under the earlier codebook; their
source/timing verification remains valid, but their analytical codes are
provisional until an explicit-source-only re-audit passes. The 15 batch-24 rows
were coded under the current rule.

`data/manual/pitch_set_aside.csv` contains no pitch codes or outcomes; it records
the search query and reason a reviewed match needs later follow-up.
`artifacts/tables/pitch_collection_status.csv` covers all 1,094 eligible matches
with `verified`, `set_aside`, or `unreviewed` source-collection status.

### Current measurement rule for final analytical pitch variables

Every final analytical pitch variable must be a **standardization of an expected
playing effect explicitly stated by the eligible pre-match source**. The researcher
does not independently diagnose the pitch.

Physical descriptions such as `dry`, `dusty`, `grassy`, `green`, `moist`, `hard`,
`cracked`, `worn`, `tacky`, or `used` may appear in the short provenance note, but
they are never converted by analyst judgment into `spin`, `pace_seam`,
`batting_ease`, `bounce_profile`, or `two_paced_expected` values. If the source
does not state an expected playing effect, the corresponding field remains blank
or `unknown`.

Before final pitch-effect modeling, every retained legacy nonblank value below must
be re-audited against the source; unsupported inferred values must be blanked or
removed.

| Variable | Type | Definition under current rule |
|---|---|---|
| `espn_match_id_candidate` | string/nullable | numeric Cricsheet ID copied as an unverified candidate; never assumed correct |
| `espn_legacy_match_url_candidate` | URL/nullable | unfetched legacy ESPN navigation candidate generated from the probable ID |
| `espn_match_id_verified` | string/nullable | actual numeric ESPN ID after human or licensed match-identity verification |
| `espn_match_url_verified` | URL/nullable | ESPNcricinfo match page confirmed against teams, date, event, and venue |
| `espn_linkage_status` | category | `unverified_candidate`, `verified_match`, `not_espn_id`, `wrong_match`, or `not_available` |
| `source_search_query` | string | outcome-blind pre-match pitch-report search query |
| `source_url` | string | direct eligible pre-match report URL |
| `source_title` | string | source article title |
| `published_at_utc` | timestamp/date | source publication time in UTC when shown; date only when sufficient to prove it preceded play |
| `accessed_at_utc` | timestamp | collection time |
| `pre_match_verified` | binary | publication verified before scheduled start |
| `coder_id` | string | anonymized coder label; AI-assisted provisional work explicitly labeled |
| `coder_confidence` | ordered category | clarity/confidence in standardizing the source's stated effect, not confidence in independently predicting the pitch |
| `pitch_primary_category` | category | final compliant value must be explicitly source-supported `batting_friendly`, `balanced`, `pace_seam`, `spin`, `slow_two_paced`, or `unknown` |
| `batting_ease` | ordinal 0–2 | final compliant value requires an explicit source statement about batting/scoring ease; blank when unstated |
| `pace_seam_support` | ordinal 0–2 | final compliant value requires an explicit source statement about pace/seam help; blank when unstated |
| `spin_support` | ordinal 0–2 | final compliant value requires an explicit source statement about spin help; blank when unstated |
| `bounce_profile` | category/nullable | final compliant value requires explicit expected bounce wording; blank when unstated |
| `two_paced_expected` | binary/nullable | final compliant value requires explicit two-paced/holding/stopping/variable-pace wording; blank when unstated |
| `dew_expected` | binary/nullable | secondary match-condition expectation explicitly stated by source; blank if unstated |
| `short_paraphrased_note` | string | short audit/provenance note that may retain physical surface descriptions; avoid long copied text |
| `exclusion_reason` | string/nullable | reason the source or row is not eligible for pitch-effect modeling |

Physical surface descriptors are provenance only. They are not primary or secondary
model fields and cannot be used to derive a playing-effect code unless the source
explicitly states that effect.

## Team strength

These variables form the pre-match baseline adjustment block. They control for confounding by prior team quality; they are not the main substantive exposure.

| Variable | Type | Definition |
|---|---|---|
| `team_1_elo_pre` | float | innings-one batting team's rating before the match date |
| `team_2_elo_pre` | float | innings-two batting team's rating before the match date |
| `elo_difference_team_1` | float | team 1 minus team 2 pre-match Elo |
| `team_1_prior_matches` | integer | all decided matches available before the match date |
| `team_2_prior_matches` | integer | all decided matches available before the match date |
| `team_1_prior20_win_rate` | float/nullable | wins in the prior 20 decided matches; blank at cold start |
| `team_2_prior20_win_rate` | float/nullable | same for team 2 |
| `team_elo_pre` | float | focal batting team's mapped pre-match rating |
| `opponent_elo_pre` | float | focal opponent's mapped pre-match rating |
| `elo_difference` | float | focal batting team minus opponent pre-match Elo |

## Historical venue conditions

These fields summarize at most 20 earlier matches at the exact recorded venue. All
matches on the same date receive the state available before that date.

| Variable | Type | Definition |
|---|---|---|
| `venue_history_available` | binary | 1 when at least one earlier-date match exists at the recorded venue |
| `venue_prior_matches` | integer | number of earlier venue matches in the rolling window |
| `venue_prior_innings` | integer | contributing regulation innings; retained for audit |
| `venue_prior_pp_runs_mean` | float/nullable | prior-window powerplay runs per innings |
| `venue_prior_pp_wickets_mean` | float/nullable | prior-window powerplay wickets per innings |
| `venue_prior_boundary_pct` | float/nullable | prior-window boundary balls divided by legal balls × 100 |
| `venue_prior_dot_ball_pct` | float/nullable | prior-window dot balls divided by legal balls × 100 |

These venue-history fields are historical scoring-environment summaries. They are
**not** pitch-condition measurements and cannot backfill or infer missing
source-stated pitch effects.

## Merge and audit fields

| Variable | Type | Definition |
|---|---|---|
| `pitch_available` | binary | current file: a source/timing-eligible provisional pitch row joined by exact match ID; final analysis requires every included row to pass the explicit-source-only rule |
| `split` | category | `development` through 2023, `validation` in 2024, or locked `locked_test` from 2025 onward |
| `exclusion_reasons` | string/list | semicolon-delimited prespecified reason codes |
| `analysis_eligible_primary` | binary | passes core cleaning and the 2015-forward men's ODI primary rules; no event restriction |
| `source_snapshot_id` | string | hash/date identifier for raw-source manifest |

## Final-model anti-leakage and measurement allowlist

The final training matrix may contain only approved powerplay, **re-audited
source-stated pre-match pitch-effect**, historical venue, pre-match team strength,
toss, innings order, venue/grouping, year, and competition-type features. Match ID
is a grouping key, not a predictor. Outcome, winner, margin, result method, full
innings total, later-match data, generic hourly weather variables, raw physical
surface descriptors, and any researcher-inferred pitch labels are prohibited.
