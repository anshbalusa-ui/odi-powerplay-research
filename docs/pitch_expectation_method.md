# Pre-match expected playing environment: measurement protocol

## Construct and amendment (2026-09-27)

Teams cannot observe the future realized pitch with certainty. This observational study now proposes a **model-estimated pre-match expected playing environment** from eligible, verified contemporaneous reporting. These are uncertain expectations, not actual pitch behavior or causal effects. The previous `source-stated pre-match pitch effects` scheme required explicit playing-effect wording and prohibited surface inference. During an incomplete human second-coder pilot, the researcher reported that approximately seven of the first ten reviewed reports left almost every historical analytical field unstated. This is a reported pilot observation, **not a validated new missingness statistic**. The construct changed **before final expectation/pitch-outcome interpretation**. Bounded pre-match, source-grounded inference is now permitted because the decision problem concerns expectations; uncertainty and disagreement remain observable. No old re-audit labels, coder notes, or previous human judgments are inputs to this new release. Historical files and strict-code scripts remain intact as the superseded explicit-source human-coded design; its unfinished 46-case human exercise is not a completed reliability study.

Decision log:

| ID / date | Outcome-blind decision | Basis / alternative | Artifacts affected |
| --- | --- | --- | --- |
| PE-001 / 2026-09-27 | Use a distinct expectation construct; retain historical strict derivative without mixing variables. | Pilot reported substantial blank fields; continuing explicit-only coding does not measure available probabilistic pre-match cues. No pitch-outcome associations consulted. | `AGENTS.md`, `config/study.yaml`, canonical rubric |
| PE-002 / 2026-09-27 | Freeze rubric v1, three independent assessors, per-field majority else `uncertain`; median confidence; overall majority and >=60 primary, any confidence broad, >=75 high, all-fields 3/3 unanimous. | Mechanical, prespecified stability gate; thresholds fixed before outcome modeling. No outcome data consulted. | `config/pitch_expectation_agent.json`, consensus scripts |
| PE-003 / 2026-09-27 | Source captures require independent pre-match review; date-only publication must safely precede verified UTC start even at 23:59:59.999999 UTC. | Contemporary URL/title and prior coder prose are insufficient evidence; date-only UTC overlap is ambiguous. No outcomes consulted. | sanitized input builder and manifest |

## Frozen rubric and variable definitions

`config/pitch_expectation_agent.json` is the canonical exact UTF-8 assessor prompt/rubric. Hash **file bytes** with SHA-256; every pass record and release stores that hash. A changed rubric requires a version increment and rerunning **all** passes, not selectively reassessing outcomes or difficult cases.

- `batting_expectation`: `difficult`, `neutral`, `favorable`, `uncertain`.
- `pace_seam_expectation`, `spin_expectation`: `low`, `neutral`, `high`, `uncertain`.
- `slow_two_paced_expectation`: `unlikely`, `possible`, `likely`, `uncertain`.
- `overall_expected_environment`: `batting_favorable`, `balanced`, `pace_seam_favorable`, `spin_slow_favorable`, `uncertain`.
- `confidence`: integer 0–100 for the **source support for the joint pre-match assessment**, not the probability that the pitch behaves that way.
- `evidence`: a short source-grounded paraphrase; `reasoning_basis`: one or more of explicit effect statement, physical surface description, contextual pre-match inference; `rationale`: short explanation. Physical cues may contribute but never mechanically set a category; contradictory signals lower confidence. `uncertain` means unresolved, not a neutral/default value.

Primary candidate effect modifier **after human approval**: overall category, not all four dimensions jointly. If categories are too sparse, simplify only on measurement semantics/cell counts before inspecting associations, then document an amendment. Proposed future contrasts involve runs and wickets, not all possible interactions. Preserve both innings in one match/fold and all locked 2025+ outcome fields unopened.

## Source universe, contamination and provenance

The tracked `pitch_reports_verified.csv` has 243 verified report records; `pitch_code_reaudit.csv` marks 14 as historically unavailable. Thus there are **229 registry candidates**, not 229 independently re-retrieved articles. A conservative new timing check leaves 227 candidates with defensible publication-before-start timing and flags two date-only records as `timing_ambiguous` pending stronger publication evidence; no old release row is relabeled. The historically compliant derivative has 229 rows; it is **not** a new expectation release. From the metadata-only 229: 168 development, 10 validation, and 51 locked source IDs; these are not newly verified subset/model-table counts.

`build_pitch_expectation_inputs.py` reads tracked source metadata and timing/registry status only, and projects a **positive allowlist** before an assessor can see it. No processed outcome/PP dataset or old coder note/code is loaded into its model payload. For each source, a separate rights-sensitive local capture is required at `data/interim/pitch_expectation_captures/<match_id>.json` (ignored by Git):

```json
{
  "source_url": "https://publisher.example/pre-match-preview",
  "published_at_utc": "2024-03-01T01:00:00Z",
  "retrieved_at_utc": "2026-09-27T12:00:00Z",
  "review_status": "pre_match_content_verified",
  "reviewer_id": "independent_review_01",
  "source_text": "Brief, independently verified pre-match relevant source content"
}
```

The capture URL and publication metadata must match the frozen registry, and the reviewer must verify article relevance, genuine pre-match origin, that the **currently retrieved content** does not contain later edits/result knowledge, and that the text faithfully captures the relevant contemporaneous section. No old coder paraphrase may substitute for original-source text. Keep raw snapshots local with retrieval timestamp and content hash; do not copy whole copyrighted articles into Git. Obvious result-page markers are blocked automatically, but a regex cannot establish temporal eligibility: reviewers must mark `needs_review`, `unavailable` or `contaminated_or_ambiguous` rather than certify an unsafe page. Missing capture is `not_retrieved`, **not proof of unavailability**. Historical source-unavailable IDs remain excluded. A date-only record whose conservative upper bound overlaps start is `timing_ambiguous` unless stronger publication timing is verified; do not fill it with a guessed timestamp. The manifest records each source status and SHA-256s of source registry, rubric, payload and verified content.

`reviewer_id` and `review_status` are auditable attestations, not proof that
the article was independently reviewed or that a live web page was never
amended. Inspect the cited source and reviewer evidence during the human
sanity audit; do not infer content validity from an automated `assessable`
count alone.

## Execution and measurement gate

Use Python 3.11+ and do not start the assessor runner until the ignored captures have passed independent review. The runner requires an actual `OPENAI_API_KEY` and provider model ID; it will not simulate assessments. The task orchestration interface does not expose per-subagent model/reasoning routing, so provider response `model` is recorded as observed version. Never imply that a configured default proves the actual model was used. Run independent passes to separate files; no pass reads another pass. Commands:

```bash
python3.11 scripts/build_pitch_expectation_inputs.py
python3.11 scripts/audit_pitch_expectations.py
python3.11 scripts/run_pitch_expectation_agents.py --assessor A --model "$LUNA_MODEL_ID" --reasoning-effort high --run-id "$FROZEN_RUN_ID"
python3.11 scripts/run_pitch_expectation_agents.py --assessor B --model "$LUNA_MODEL_ID" --reasoning-effort high --run-id "$FROZEN_RUN_ID"
python3.11 scripts/run_pitch_expectation_agents.py --assessor C --model "$SOL_MODEL_ID" --reasoning-effort high --run-id "$FROZEN_RUN_ID"
python3.11 scripts/build_pitch_expectation_consensus.py
```

Set `OPENAI_API_KEY`, `LUNA_MODEL_ID`, `SOL_MODEL_ID`, and `FROZEN_RUN_ID` to real available provider/model/run identifiers before execution. Complete, hashed A/B/C passes are required before the consensus builder will write a release. Majority is calculated **separately for each categorical field**; three-way disagreements yield `uncertain`; median confidence and the four gates are deterministic. A source with no safe original content is not assessed. `artifacts/tables/pitch_expectation_agreement.json` reports per-field and pairwise exact agreement, Cohen's kappa only when mathematically defined, distribution by year/provider/competition/development/2024/locked and sparse category cells. These are **model-assessment stability** metrics, not pitch truth or human intercoder reliability. `artifacts/tables/pitch_expectation_human_audit.csv` selects up to 15 varied cases deterministically; human rates pre-match relevance, evidence support, interpretive reasonableness, and leakage/hallucination with `pass`, `questionable`, `fail` plus note; worksheet cells stay blank until reviewed.

The frozen Cricsheet raw snapshot and generated model table are absent in the fresh clone; source metadata counts must not be presented as independently reproduced modern cohort or paired innings totals. The consensus report marks `cohort_pairing_verified=false`; verify cohort pairing from the snapshot after approval, without opening locked outcomes.

**Stop before outcome modeling.** With zero completed A/B/C passes, classify the current measurement as `PITCH_EXPLORATORY_ONLY` (no substantive pitch analysis is permissible); re-evaluate from actual stability and source coverage when passes exist. No empty release, invented scores/agreement, or fake audit. The historical `run_pitch_interaction_analysis.py` remains a legacy script and must not be run for these new variables. Full-cohort results are not modified. Final model-table build, associations, 2024 evaluation, figures and abstract claims require explicit human approval and a separate expectation-specific modeling path. Every measurement manifest keeps `locked_test_scored=false`.
