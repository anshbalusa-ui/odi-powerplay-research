# Pre-Match Pitch Coding Codebook

## Purpose

Convert pre-match prose into auditable variables without reading the outcome. Code only claims about the playing surface or expected surface behavior. Weather belongs in the weather table, though `dew_expected` may capture a report's pre-match expectation.

## Source eligibility

A source is eligible when:

- it is an ESPNcricinfo preview, pitch/conditions report, or pre-match analysis;
- its publication time can be shown to precede match start;
- it discusses the specific match venue/surface, not only generic venue history;
- it does not reveal any match event or result.

If these conditions fail, set `pre_match_verified = 0` and record `exclusion_reason`. Store a short paraphrase, not a large copied passage.

## Primary category

Choose one category based on the strongest explicit expectation. If two are equally supported, use `balanced` and capture both in the dimensions.

| Value | Coding rule |
|---|---|
| `batting_friendly` | Explicitly good/flat for batting, high scoring, little expected assistance |
| `balanced` | Expected to offer meaningful help to both batting and bowling, or mixed evidence |
| `pace_seam` | Pace, seam, swing, bounce, grass, or lateral movement is the main expectation |
| `spin` | Turn, grip, or spin assistance is the main expectation |
| `slow_two_paced` | Slowness, stopping, variable pace, or difficult timing is the main expectation |
| `unknown` | Report lacks enough surface-specific evidence |

## Ordinal dimensions

Use integer values `0`, `1`, `2`, or blank. Blank means not stated/insufficient evidence; zero means the report affirmatively indicates absence or the opposite.

| Field | 0 | 1 | 2 |
|---|---|---|---|
| `batting_ease` | difficult | balanced/mixed | easy/high-scoring |
| `pace_support` | little | some | strong |
| `spin_support` | little | some/later | strong/early |
| `grass_cover` | bare/little | some | substantial |
| `surface_moisture` | dry | neutral/unclear level stated | damp/moist |
| `hardness` | soft | medium | hard |
| `dryness` | moist/not dry | moderate | very dry |
| `visible_cracks` | none | minor | prominent |

## Binary/ternary dimensions

- `two_paced_expected`: `1` yes, `0` explicitly no, blank unstated.
- `dew_expected`: `1` yes, `0` explicitly no, blank unstated.
- `expected_par_score`: numeric only when the report gives a clear expected par or narrow range; use the midpoint of a range and note the original range in the paraphrase.

## Confidence

| Value | Meaning |
|---|---|
| `high` | direct, unambiguous description of the specific surface |
| `medium` | relevant description but mixed or partly inferred |
| `low` | vague, generic, or difficult to map; retain for audit and consider excluding |

## Coding procedure

1. Create the match row and verify identifiers/date/venue.
2. Confirm publication precedes match start.
3. Read only the eligible pre-match source.
4. Write a short neutral paraphrase.
5. Assign dimensions first, then the primary category.
6. Record coder and confidence.
7. Do not inspect scorecard or outcome while coding.
8. Independently double-code a random 20% sample stratified by year.
9. Freeze the codebook before resolving disagreements.

## Reliability analysis

- Report percentage agreement for the primary category.
- Report Cohen's kappa for the primary category and binary fields.
- Report weighted Cohen's kappa for ordinal dimensions.
- Show a disagreement table and document consensus changes.

Do not silently rewrite categories after looking at model performance.

