# Pre-Match Pitch Coding Codebook

## Purpose

Convert pre-match prose into auditable variables without reading the outcome. Code the expected playing-surface behavior: scoring ease, pace/seam assistance, spin assistance, bounce, and two-paced behavior. Generic weather measurements are outside the primary design; `dew_expected` is retained only when a pre-match report explicitly mentions it.

## Source eligibility

A source is eligible when:

- it is a match-specific ESPNcricinfo preview, pitch/conditions report, or another clearly identified reputable pre-match source when ESPN has no eligible report;
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
| `pace_seam` | Pace, seam, carry, bounce, grass, or lateral movement is the main expectation |
| `spin` | Turn, grip, or spin assistance is the main expectation |
| `slow_two_paced` | Slowness, stopping, variable pace, or difficult timing is the main expectation |
| `unknown` | Report lacks enough surface-specific evidence |

## Primary model dimensions

Use integer values `0`, `1`, `2`, or blank. Blank means not stated/insufficient evidence; zero means the report affirmatively indicates absence or the opposite.

| Field | 0 | 1 | 2 |
|---|---|---|---|
| `batting_ease` | difficult | balanced/mixed | easy/high-scoring |
| `pace_seam_support` | little | some | strong |
| `spin_support` | little | some/later | strong/early |

`bounce_profile` is categorical because low, steep, and variable bounce are not points on one simple scale:

| Value | Coding rule |
|---|---|
| `low` | Explicitly low, skiddy, or staying down |
| `standard` | Explicitly normal, even, predictable, or true bounce |
| `steep` | Explicit extra, steep, or pronounced bounce/carry |
| `variable` | Explicit uneven, inconsistent, or unpredictable bounce |
| blank | Bounce is not stated clearly enough to code |

## Binary dimensions

- `two_paced_expected`: `1` yes, `0` explicitly no, blank unstated.
- `dew_expected`: `1` yes, `0` explicitly no, blank unstated. This is a secondary match-condition field, not a pitch-surface feature.

Grass, moisture, hardness, dryness, cracks, and stated par scores may be summarized in `short_paraphrased_note` when they explain a code. They are not separate primary predictors.

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
