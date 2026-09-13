# Pre-Match Pitch Coding Codebook

## Purpose

Convert pre-match prose into auditable variables without reading the outcome. Keep two concepts separate:

1. **Physical surface conditions/descriptors** — what the report says the pitch itself is like, such as grassy, moist, dry, dusty, hard, soft/tacky, worn, cracked, or used.
2. **Expected playing behavior** — how the report expects that surface to play, such as batting-friendly, pace/seam-supportive, spin-supportive, or slow/two-paced.

The expected playing-behavior variables are the main analytical pitch variables. Physical surface descriptors are retained as source evidence and for interpretation; they must not be treated as automatic substitutes for expected behavior. For example, a dry pitch is not automatically coded as spin-supportive unless the eligible pre-match report explicitly supports that expectation.

Generic weather measurements are outside the primary design; `dew_expected` is retained only when a pre-match report explicitly mentions it.

## Source eligibility

A source is eligible when:

- it is a match-specific ESPNcricinfo preview, pitch/conditions report, or another clearly identified reputable pre-match source when ESPN has no eligible report;
- its publication time can be shown to precede match start;
- it discusses the specific match venue/surface, not only generic venue history;
- it does not reveal any match event or result.

If these conditions fail, set `pre_match_verified = 0` and record `exclusion_reason`. Store a short paraphrase, not a large copied passage.

## Physical surface conditions/descriptors

Record only descriptors explicitly stated or clearly described in the eligible pre-match source. These are descriptions of the surface itself, not conclusions about how it will necessarily play.

Typical descriptors include:

| Surface descriptor | Meaning in the source description |
|---|---|
| `grassy_green` | Visible grass/green covering or a notably grassed surface |
| `moist` | Moisture, dampness, or freshness in/on the surface |
| `dry_dusty` | Dry, dusty, abrasive, or powdery surface |
| `hard` | Firm, hard, compact surface |
| `soft_tacky` | Soft, tacky, sticky, or holding surface |
| `worn_cracked` | Worn, cracked, deteriorating, or visibly breaking surface |
| `used_surface` | Previously used strip or surface explicitly described as used |
| `flat_true` | Flat/even physical surface or explicitly true, consistent bounce |

These descriptors are **not deterministic rules**. A grassy pitch does not automatically become `pace_seam`; a dry pitch does not automatically become `spin`; and a hard surface does not automatically become `batting_friendly`. Code expected playing behavior only when the report itself supports that expectation.

When a source gives a physical descriptor but does not state or clearly support a playing effect, retain the descriptor in the audit record/short paraphrase and leave the corresponding expected-behavior field unstated rather than guessing.

## Primary expected-playing-behavior category

Choose one category based on the strongest explicit pre-match expectation of how the pitch will play. If two effects are equally supported, use `balanced` and capture both in the model dimensions.

| Value | Coding rule |
|---|---|
| `batting_friendly` | Explicitly expected to be good/flat for batting, high scoring, or offer little bowling assistance |
| `balanced` | Expected to offer meaningful opportunities to both batting and bowling, or mixed evidence with no dominant effect |
| `pace_seam` | Pace, seam, carry, bounce, or lateral movement is the main expected playing effect |
| `spin` | Turn, grip, or spin assistance is the main expected playing effect |
| `slow_two_paced` | Slowness, stopping, variable pace, or difficult timing is the main expected playing effect |
| `unknown` | Report lacks enough surface-specific evidence to infer expected playing behavior |

### Typical links between surface conditions and expected behavior

These are interpretation aids, not automatic coding rules:

- **Pace/seam-supportive:** reports may mention a green/grassy or moist surface, hardness/carry, pronounced bounce, or expected lateral movement. The category is assigned because the report expects meaningful help for fast bowlers, not merely because grass or moisture is present.
- **Spin-supportive:** reports may mention a dry, dusty, worn, cracked, abrasive, or gripping surface. The category is assigned because the report expects turn/grip/spin assistance, not merely because the surface is dry.
- **Slow/two-paced:** reports may mention a dry/tired, used, soft/tacky, or inconsistent surface where the ball may hold, stop, or arrive at different speeds. The defining expectation is difficult timing or inconsistent pace off the pitch.
- **Batting-friendly:** reports may mention a flat, hard, even, true surface with predictable bounce and little expected lateral movement or grip. The defining expectation is easy/consistent scoring conditions.
- **Balanced:** the report gives credible support for multiple effects without one clearly dominating, such as early seam followed by good batting conditions or later spin without the surface being strongly spin-dominant overall.

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

Physical descriptors such as grass, moisture, hardness, dryness, dust, cracks, tackiness, or a used surface should be preserved as provenance/audit evidence when stated. They are not treated as interchangeable with the expected-playing-behavior variables.

## Confidence

| Value | Meaning |
|---|---|
| `high` | direct, unambiguous description of the specific surface and/or its expected behavior |
| `medium` | relevant description but mixed or partly inferred from the source's wording |
| `low` | vague, generic, or difficult to map; retain for audit and consider excluding |

## Coding procedure

1. Create the match row and verify identifiers/date/venue.
2. Confirm publication precedes match start.
3. Read only the eligible pre-match source.
4. Write a short neutral paraphrase that distinguishes physical surface description from expected playing behavior.
5. Record any explicitly stated physical surface descriptors.
6. Assign expected-behavior dimensions first, then the primary expected-playing-behavior category.
7. Record coder and confidence.
8. Do not inspect scorecard or outcome while coding.
9. Independently double-code a random 20% sample stratified by year.
10. Freeze the codebook before resolving disagreements.

## Reliability analysis

- Report percentage agreement for the primary expected-playing-behavior category.
- Report Cohen's kappa for the primary category and binary fields.
- Report weighted Cohen's kappa for ordinal dimensions.
- Show a disagreement table and document consensus changes.

Do not silently rewrite categories after looking at model performance.
