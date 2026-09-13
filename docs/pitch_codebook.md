# Pre-Match Pitch-Effect Coding Codebook

## Purpose

Convert eligible pre-match prose into auditable **source-stated pitch-effect variables** without reading the outcome.

The core rule is strict: **code only the playing effects explicitly stated by the eligible pre-match source. Do not perform independent pitch analysis.** The project does not infer spin from a dry/dusty surface, pace/seam from grass or moisture, batting ease from hardness/flatness, or slow/two-paced behavior from a used or worn surface unless the source itself explicitly states the corresponding playing effect.

Physical descriptions such as grass, moisture, dryness, dust, hardness, cracks, wear, or a used strip may be preserved in `short_paraphrased_note` as provenance. They are not model features and cannot be used by the coder to manufacture an unstated pitch effect.

Generic weather measurements are outside the primary design; `dew_expected` is retained only when an eligible pre-match report explicitly mentions it.

## Source eligibility

A source is eligible when:

- it is a match-specific ICC, national-board, established news, or established specialist-cricket pre-match report; ESPN is eligible only through the separately documented human/licensed route;
- its publication time can be shown to precede match start;
- it discusses the specific match venue/surface or explicitly states how that pitch is expected to play;
- it does not reveal any match event or result.

If these conditions fail, set `pre_match_verified = 0` and record `exclusion_reason`. Store a short paraphrase, not a large copied passage.

AI-assisted coding may produce a provisional first pass for eligible non-ESPN sources when the `coder_id` discloses that status. It does not satisfy the independent-human reliability requirement. ESPN source collection and linkage remain restricted to a human or licensed route under the reviewed terms.

### ESPN match identity

The queue's numeric Cricsheet ID and legacy ESPN URL are unverified navigation candidates. Before coding an ESPN source, compare teams, date, event, and venue; record the actual `espn_match_id_verified` and `espn_match_url_verified`; then set `espn_linkage_status = verified_match`. Use `wrong_match` or `not_espn_id` when the candidate fails. A candidate alone is never evidence and must not be bulk-opened by automation. An ESPN row cannot be `pre_match_verified = 1` until match linkage is human- or license-verified.

### Match-start verification

Create `data/manual/match_start_times.csv` from the tracked start-time template. Verify teams, local date, event, and venue against a cited schedule or match page; record the scheduled local datetime, the venue's IANA timezone, the converted UTC datetime, source provenance, and verifier. Set `start_time_status=verified` only after `audit_match_start_times.py` accepts the identity and conversion. Pending, unavailable, rejected, or structurally invalid timestamps are never passed to pitch validation. Keep this metadata-only task separate from pitch-effect coding so scorecard or result information cannot influence the category.

## Non-inference rule

The coder is transcribing and standardizing a source's stated expectation, not diagnosing the pitch.

Examples:

- Source says **"dry and cracked"** but gives no expected playing effect -> preserve that description in the short paraphrase; leave spin/pace/batting/two-paced effects unstated.
- Source says **"dry surface expected to assist spin"** -> code the stated spin effect.
- Source says **"there is grass on the pitch"** but does not say it should help seam/pace -> do not code pace/seam support from the grass alone.
- Source says **"the surface should offer movement for the seamers"** -> code the stated pace/seam effect, whether or not grass is mentioned.
- Source says **"hard, true surface expected to be good for batting"** -> code the stated batting effect; the physical description is only supporting provenance.

No model variable may be derived solely from the researcher's own interpretation of a physical pitch descriptor.

## Primary source-stated behavior category

Choose one category based on the strongest **explicitly stated** pre-match expectation. If two effects are explicitly stated with no clear dominant effect, use `balanced` and capture the stated dimensions. If the report describes the surface but does not explicitly state how it is expected to play, use `unknown` rather than inferring a category.

| Value | Coding rule |
|---|---|
| `batting_friendly` | Source explicitly states that batting/scoring should be easy, high-scoring, flat/true for batting, or that bowlers should receive little assistance |
| `balanced` | Source explicitly states meaningful opportunity for both batting and bowling, or explicitly states multiple playing effects with no dominant expectation |
| `pace_seam` | Source explicitly states that pace, seam, carry, bounce, or lateral movement should materially assist fast bowlers |
| `spin` | Source explicitly states that turn, grip, or spin assistance is expected |
| `slow_two_paced` | Source explicitly states that the pitch should be slow, hold/stop, play two-paced, vary in pace, or make timing difficult |
| `unknown` | Eligible source does not explicitly state enough about expected playing behavior to assign a category |

## Primary model dimensions

Use integer values `0`, `1`, `2`, or blank. **Every nonblank value must be supported by an explicit source statement about the expected playing effect.** Blank means unstated/insufficient evidence; zero means the source explicitly indicates little/no support or the opposite effect.

| Field | 0 | 1 | 2 |
|---|---|---|---|
| `batting_ease` | source explicitly expects difficult batting/scoring | source explicitly expects mixed/balanced batting conditions | source explicitly expects easy/high-scoring batting conditions |
| `pace_seam_support` | source explicitly expects little/no pace-seam help | source explicitly expects some pace-seam help | source explicitly expects strong pace-seam help |
| `spin_support` | source explicitly expects little/no spin help | source explicitly expects some/later spin help | source explicitly expects strong/early spin help |

`bounce_profile` is coded only when the source explicitly describes the expected bounce behavior:

| Value | Coding rule |
|---|---|
| `low` | Source explicitly expects low, skiddy, or staying-down bounce |
| `standard` | Source explicitly expects normal, even, predictable, or true bounce |
| `steep` | Source explicitly expects extra, steep, or pronounced bounce/carry |
| `variable` | Source explicitly expects uneven, inconsistent, or unpredictable bounce |
| blank | Expected bounce behavior is not stated clearly enough to code |

## Binary dimensions

- `two_paced_expected`: `1` only when the source explicitly expects two-paced/holding/stopping or variable pace; `0` only when it explicitly says otherwise; blank when unstated.
- `dew_expected`: `1` yes, `0` explicitly no, blank unstated. This is a secondary match-condition field, not a pitch-surface feature.

Physical descriptors such as grass, moisture, hardness, dryness, dust, cracks, tackiness, wear, or a used surface may be retained in `short_paraphrased_note` for provenance. **They are never converted into model fields by analyst inference.**

## Confidence

| Value | Meaning |
|---|---|
| `high` | direct, unambiguous source statement about the expected playing effect |
| `medium` | source states the expected effect but with mixed/qualified wording |
| `low` | source wording is vague or difficult to standardize; retain for audit and consider excluding |

Confidence refers to clarity of the source's stated effect, not the coder's personal confidence about how the pitch will actually behave.

## Coding procedure

1. Create the match row and verify identifiers/date/venue.
2. Confirm publication precedes match start.
3. Read only the eligible pre-match source.
4. Write a short neutral paraphrase separating factual physical description from the source's stated expected playing effect.
5. Code only explicitly stated expected-effect dimensions.
6. Assign the primary source-stated behavior category from those explicit statements; use `unknown` if the effect is not stated.
7. Record coder and confidence.
8. Do not inspect scorecard or outcome while coding.
9. Independently double-code a random 20% sample stratified by year.
10. Freeze the codebook before resolving disagreements.

## Reliability analysis

- Report percentage agreement for the primary source-stated behavior category.
- Report Cohen's kappa for the primary category and binary fields.
- Report weighted Cohen's kappa for ordinal dimensions.
- Show a disagreement table and document consensus changes.

Do not silently rewrite categories after looking at model performance. Do not add an unstated pitch effect based on cricket knowledge, venue reputation, physical surface description, or match outcome.
