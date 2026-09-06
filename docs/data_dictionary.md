# Data Dictionary

## Dataset levels

| Dataset | Grain | Purpose |
|---|---|---|
| `cricsheet_matches` | one match | stable match metadata and result |
| `powerplay_innings` | one regulation team-innings | first-10-over statistics and context |
| `pitch_reports` | one match/source | pre-match prose provenance and human codes |
| `team_strength_pre` | one match/team | ratings calculated before the match date |
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

## Pitch fields

| Variable | Type | Definition |
|---|---|---|
| `source_url` | string | direct eligible pre-match report URL |
| `published_at_utc` | timestamp | source publication time |
| `accessed_at_utc` | timestamp | collection time |
| `pre_match_verified` | binary | publication verified before scheduled start |
| `coder_id` | string | anonymized coder label |
| `coder_confidence` | ordered category | low, medium, high |
| `pitch_primary_category` | category | batting-friendly, balanced, pace/seam, spin, slow/two-paced, unknown |
| `batting_ease` | ordinal 0–2 | difficult to easy/high-scoring |
| `pace_seam_support` | ordinal 0–2 | little to strong pace/seam help |
| `spin_support` | ordinal 0–2 | little to strong spin help |
| `bounce_profile` | category/nullable | low, standard, steep, variable, or blank when unstated |
| `two_paced_expected` | binary/nullable | report expectation; blank if unstated |
| `dew_expected` | binary/nullable | secondary match-condition expectation; blank if unstated |
| `short_paraphrased_note` | string | short audit note; avoid long copied text |

Descriptions of grass, moisture, hardness, dryness, cracks, or par scores remain in `short_paraphrased_note` when they support the coded behavior. They are not separate primary model fields.

## Team strength

These variables form the pre-match baseline adjustment block. They control for confounding by prior team quality; they are not the main substantive exposure.

| Variable | Type | Definition |
|---|---|---|
| `team_elo_pre` | float | focal team rating before match date |
| `opponent_elo_pre` | float | opposing team rating before match date |
| `elo_difference` | float | team minus opponent pre-match Elo |
| `team_prior20_win_rate` | float/nullable | wins among prior 20 decided ODIs |
| `opponent_prior20_win_rate` | float/nullable | same for opponent |

## Merge and audit fields

| Variable | Type | Definition |
|---|---|---|
| `pitch_join_status` | category | exact ID, composite verified, unmatched, ambiguous |
| `exclusion_reasons` | string/list | semicolon-delimited prespecified reason codes |
| `analysis_eligible_primary` | binary | passes core cleaning and the 2015-forward men's ODI primary rules; no event restriction |
| `source_snapshot_id` | string | hash/date identifier for raw-source manifest |

## Final-model anti-leakage allowlist

The final training matrix may contain only approved powerplay, pre-match pitch, pre-match team strength, toss, innings order, venue/grouping, year, and competition-type features. Match ID is a grouping key, not a predictor. Outcome, winner, margin, result method, full innings total, later-match data, and generic hourly weather variables are prohibited.
