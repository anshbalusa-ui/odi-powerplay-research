# Agent Working Agreement

This repository is a research project, not only a prediction demo. Changes must preserve reproducibility, source provenance, the observational claim boundary, and the locked-test protocol.

## Before changing anything

- Read the current `main` version of the file before editing because another agent may have changed it.
- Keep commits small and descriptive.
- Do not unlock or inspect 2025–2026 test outcomes until the research/model freeze permits it.
- Do not introduce a new research variable or reinterpret an existing one without updating the relevant methodology/config documentation.

## Non-negotiable research rules

1. **Primary cohort:** clean men's ODIs from 2015 through the fixed Cricsheet snapshot; World Cups are a subgroup, not the main cohort.
2. **Powerplay window:** Cricsheet overs indexed 0 through 9; preserve documented legal-ball and edge-case rules.
3. **Core powerplay features:** runs, wickets lost, boundary-ball percentage, dot-ball percentage, legal-ball count, and delivery-event count.
4. **Outcome:** `batting_team_won`; both innings from a match stay in the same split/fold.
5. **Team strength:** pre-match Elo and sensitivity ratings use only earlier dates; same-date updates are batched.
6. **Pitch-source timing:** a pitch report must be demonstrably published before the verified scheduled match start.
7. **Outcome-blind pitch collection:** source discovery/coding must not expose winner, powerplay score, wickets, final score, or other match outcomes.
8. **No post-match evidence:** live commentary, result articles, post-match pitch descriptions, and later observed conditions cannot populate pre-match predictors.
9. **Claim boundary:** this is retrospective observational research; use associational/predictive language, not causal claims.
10. **Missingness:** missing source-stated pitch effects remain missing/unknown; never fabricate or backfill them.

## Critical pitch-measurement rule: source-stated effects only

**Absolutely no independent researcher/agent pitch diagnosis is allowed.**

The analytical pitch variables are standardized versions of **expected playing effects explicitly stated in eligible pre-match sources**. The agent/coder's job is to record what the source says, not to use cricket knowledge to decide how a physical surface should behave.

Examples of prohibited inference:

- `dry`, `dusty`, or `cracked` -> do **not** infer `spin`;
- `grass`, `green`, or `moist` -> do **not** infer `pace_seam`;
- `hard` or `flat` -> do **not** infer `batting_friendly`;
- `used`, `worn`, or `tacky` -> do **not** infer `slow_two_paced`.

Those physical descriptors may be retained in `short_paraphrased_note` for provenance only. They may populate an analytical effect field **only when the source itself explicitly states that expected playing effect**.

Examples of permitted coding:

- source says the surface is expected to assist spin/turn/grip -> code the stated spin effect;
- source says seamers should get movement/carry/pace assistance -> code the stated pace/seam effect;
- source says batting should be easy/high-scoring -> code the stated batting-ease effect;
- source says the pitch should be slow, hold, stop, or play two-paced -> code the stated slow/two-paced effect.

If an eligible source describes the physical surface but does not state the playing effect, leave the effect field blank or `unknown`. Never infer it.

## Existing 228-match release

The 228-match pitch-code input release predates this stricter
explicit-source-only rule, so its original fields remain labeled as legacy
provenance rather than final analytical codes. The completed re-audit is recorded
in `data/manual/pitch_code_reaudit.csv`: 169 rows passed revised, 45 passed
unchanged, and 14 are source-unavailable. The strict analytical derivative
excludes those 14 unavailable rows and applies only the re-audited fields.

For any final pitch-effect paper claim:

1. use the compliant derivative, never the mixed-status input;
2. confirm that every nonblank analytical pitch-effect value is explicitly
   supported by the source;
3. retain source-unavailable rows as excluded rather than inferred `unknown`;
4. run the independent double-coding reliability sample using the same strict rule;
5. reconcile and report reliability before presenting a final pitch interaction.

Do not describe the 228 original fields as fully compliant source-stated effects;
describe the re-audited derivative and its exclusions precisely.

## Pitch provenance and reliability

For every coded report retain the Cricsheet match ID, source URL/title, publication time, verified scheduled start, access time, coder ID, confidence, source-stated codes, and a short paraphrase. Do not copy large source passages.

Independent recoders must follow the same explicit-source-only rule. Reliability measures agreement in standardizing source statements, not agreement in independently judging the physical pitch.

## Venue history

Rolling venue-history variables are prior scoring-environment summaries only. They are not measurements of the focal match's prepared pitch and cannot fill missing source-stated pitch effects.

## Engineering rules

- Follow test-driven development for behavior changes.
- Unit tests: `python -m unittest discover -s tests -v`.
- Compile check: `python -m compileall -q src scripts`.
- Keep generated raw/interim/processed datasets out of Git unless the repository's documented release policy explicitly allows a minimized derived release.
- Never overwrite raw source snapshots; retain URL, retrieval timestamp, and checksum/manifest.
- Raise on duplicate match-level context rows rather than silently multiplying team-innings rows.
- Any model feature allowlist must reject raw source prose, physical surface descriptors, outcome fields, future information, and researcher-inferred pitch labels.

## Required documentation language

Prefer **`source-stated pre-match pitch effects`**, **`source-stated pitch behavior`**, or **`verified pre-match report expectations`** when describing analytical variables that have passed the current explicit-source-only rule. Do not imply that the researchers directly measured or independently assessed the physical pitch.
