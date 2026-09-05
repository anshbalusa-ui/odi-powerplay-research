# Transformation and Audit Log

This file defines the required transformation trail. Each completed run should produce `artifacts/run_manifest.json` containing the code commit/hash, configuration hash, input checksums, timestamps, package versions, row counts, exclusions, and output checksums.

| Step | Input | Transformation | Output | Required checks |
|---|---|---|---|---|
| 01 | Cricsheet ODI ZIP | download without modifying content; calculate SHA-256; safe extract | `data/raw/cricsheet/` + source manifest | URL, UTC retrieval time, archive hash, JSON count |
| 02 | each match JSON | validate ODI; parse stable metadata/result | match table | unique `match_id`; two teams; valid date |
| 03 | regulation innings | restrict delivery events to over indexes 0–9; compute documented measures | `powerplay_innings` | manually reconcile random matches; denominator tests |
| 04 | match table | apply prespecified cohort flags without deleting rows | cohort audit table | every exclusion has reason; count flow |
| 05 | prior decided matches | calculate date-batched Elo and prior-20 win rates | `team_strength_pre` | no focal/future match in history |
| 06 | eligible pre-match reports | paraphrase and code using frozen codebook | `pitch_reports` | source time precedes start; double-code ≥20% |
| 07 | venue list | manually canonicalize venue/coordinates/timezone | venue crosswalk | no ambiguous canonical names |
| 08 | coordinates + match date | retrieve and save unmodified 24-hour API response | `weather_hourly_raw` | request URL/params; units; 24/23/25-hour DST cases |
| 09 | hourly weather + scheduled start | select nearest start-hour value; derive sensitivity window | `weather_match_features` | offset recorded; no full-day feature in model |
| 10 | match ID/date/venue | merge pitch/weather/strength into innings | merged audit table | join cardinality; unmatched and duplicate reports |
| 11 | merged table | enforce leakage allowlist; create primary/secondary feature sets | `model_team_innings` | forbidden-column assertion |
| 12 | model table | order by date; build grouped chronological development/test sets | split manifest | match IDs never cross partitions |
| 13 | development folds | fit all preprocessing and tune models inside rolling folds | fitted candidates | test period untouched |
| 14 | locked test | create probabilities once per frozen model | predictions | range [0,1]; one row/model/eligible row |
| 15 | predictions | calculate metrics and match-cluster bootstrap CIs | metrics tables | fixed seed; failed bootstrap count |
| 16 | fitted models + test data | calibration, marginal predictions, importance, SHAP | figures/tables | labels/units; no causal language |

## Standard exclusion codes

- `NON_ODI`
- `OUT_OF_SCOPE_GENDER`
- `OUT_OF_SCOPE_YEAR`
- `OUT_OF_SCOPE_EVENT`
- `NOT_TWO_REGULATION_INNINGS`
- `TIE`
- `NO_RESULT`
- `UNKNOWN_RESULT`
- `DLS_OR_REVISED_TARGET`
- `INCOMPLETE_POWERPLAY`
- `MISSING_MATCH_METADATA`
- `PITCH_NOT_PREMATCH`
- `PITCH_SOURCE_UNMATCHED`
- `WEATHER_COORDINATES_MISSING`
- `SCHEDULED_START_MISSING`
- `WEATHER_API_MISSING`

## Join policy

1. Prefer exact `cricsheet_match_id`.
2. Validate exact ID joins against match date, canonical venue, and unordered team pair.
3. If ID is unavailable, propose a composite date + canonical venue + unordered team pair match.
4. Accept a composite match only when it is unique and human-verified.
5. Never silently choose among multiple candidates.
6. Pitch/weather are match-level tables and must remain one-to-one with `match_id` before expanding to two innings rows.

## Missing data policy

- Preserve blank/unknown separately from a genuine zero.
- Report missingness by year, venue, and outcome before modeling.
- For the primary model, categorical unknowns can use an explicit `unknown` level; numeric imputation must be learned in each training fold and accompanied by missingness indicators where justified.
- Run a complete-case sensitivity analysis.
- Do not fill missing pitch or weather using match reports written after play.

## Provenance fields required in every derived file

- `source_snapshot_id`
- `pipeline_version`
- `transformed_at_utc`
- `config_sha256`

For publication tables, remove machine-specific file paths but retain hashes and source URLs.

