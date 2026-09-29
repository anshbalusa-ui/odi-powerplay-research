# Pre-match expected playing environment: measurement protocol

## Construct and amendment (2026-09-27)

Teams cannot observe the future realized pitch with certainty. This observational study now proposes a **model-estimated pre-match expected playing environment** from eligible, verified contemporaneous reporting. These are uncertain expectations, not actual pitch behavior or causal effects. The previous `source-stated pre-match pitch effects` scheme required explicit playing-effect wording and prohibited surface inference. During an incomplete human second-coder pilot, the researcher reported that approximately seven of the first ten reviewed reports left almost every historical analytical field unstated. This is a reported pilot observation, **not a validated new missingness statistic**. The construct changed **before final expectation/pitch-outcome interpretation**. Bounded pre-match, source-grounded inference is now permitted because the decision problem concerns expectations; uncertainty and disagreement remain observable. No old re-audit labels, coder notes, or previous human judgments are inputs to this new release. Historical files and strict-code scripts remain intact as the superseded explicit-source human-coded design; its unfinished 46-case human exercise is not a completed reliability study.

Decision log:

| ID / date | Outcome-blind decision | Basis / alternative | Artifacts affected |
| --- | --- | --- | --- |
| PE-001 / 2026-09-27 | Use a distinct expectation construct; retain historical strict derivative without mixing variables. | Pilot reported substantial blank fields; continuing explicit-only coding does not measure available probabilistic pre-match cues. No pitch-outcome associations consulted. | `AGENTS.md`, `config/study.yaml`, canonical rubric |
| PE-002 / 2026-09-27 | Freeze rubric v1, three independent assessors, per-field majority else `uncertain`; median confidence; overall majority and >=60 primary, any confidence broad, >=75 high, all-fields 3/3 unanimous. | Mechanical, prespecified stability gate; thresholds fixed before outcome modeling. No outcome data consulted. | `config/pitch_expectation_agent.json`, consensus scripts |
| PE-003 / 2026-09-27 | Source captures require independent pre-match review; date-only publication must safely precede verified UTC start even at 23:59:59.999999 UTC. | Contemporary URL/title and prior coder prose are insufficient evidence; date-only UTC overlap is ambiguous. No outcomes consulted. | sanitized input builder and manifest |
| PE-004 / 2026-09-28 | Quarantine HTML snapshots locally; require article publication **and last modification** before start, a short article-scoped condition excerpt, score/result screening, and independent excerpt review before model input. | A publication timestamp does not authenticate later page contents. Excluding temporally ambiguous, inaccessible, amended, or contaminated pages avoids leaking outcomes at the cost of severe coverage loss. No outcome fields consulted. | source collector, review dispositions, ignored captures |
| PE-005 / 2026-09-28 | Before any new pitch/outcome analysis, rescreen frozen original-source snapshots using focal-article JSON-LD when article markup lacks text; retain only condition sentences without result/score markers. Quarantine any article containing explicit result/live-coverage markers, any later modification, or unresolved article identity/timing; independently review every surviving excerpt. Preserve the earlier five-source run as superseded, never selectively reuse its assessments when the input set changes. | The original paragraph-level screen missed article bodies at several publishers and discarded otherwise pre-match condition sentences adjacent to historical-match recaps. Filtering those recaps before a reviewer or assessor sees text can improve coverage, but the article metadata and sanitized excerpt still require individual review and cannot prove an unamended page. No pitch/outcome associations consulted. | source extractor, append-only retrieval snapshots, separate source review and assessor run directories |


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

The capture URL and publication metadata must match the frozen registry. Reviewers inspect only screened, article-scoped excerpts and source provenance, not raw pages that might expose outcomes. They must reject excerpts without focal-match relevance, source-supported pre-match timing, or safe condition evidence. The source collector quarantines immutable original HTML locally with retrieval time and checksum; it checks publisher publication and last-modification metadata before extracting condition sentences, drops sentences with score/result markers, and quarantines result/live pages or any later edits. No old coder paraphrase may substitute for original-source text. A regex or publisher timestamp cannot alone establish that a current page was never amended. Missing capture is `not_retrieved`, **not proof of unavailability**; unknown timing is `timing_ambiguous`, never guessed.

`reviewer_id` and `review_status` attest to the screened excerpt review, not to the
truth of a publisher's last-modification field or to ground-truth playing conditions.
During the human sanity audit, inspect the outcome-blinded evidence and provenance;
seek independent contemporaneous source verification where possible. If original
content validity remains unresolved, record `questionable` rather than asserting
accuracy. Do not infer validity from an automated `assessable` count.

## Execution and measurement gate

Use Python 3.11+ and do not start either assessor runner until the ignored captures have passed independent review. The API runner requires `OPENAI_API_KEY` and returns the provider response model identifier. The installed Codex CLI adapter is an authenticated alternative when no API key exists: it routes requested `gpt-5.6-luna` for A/B and `gpt-6-sol` for C with reasoning effort `high`; the CLI reveals its version and requested route, **not** the provider's actual model build identifier. Each CLI invocation runs in a fresh temporary directory with read-only sandbox, user config/rules disabled and ephemeral session; the adapter rejects any tool-use event. The routing and event checks do not prove an independently observable server-side model build. Neither runner forwards other assessors' records. The canonical rubric file is hashed independently of each source payload. Commands for the CLI route:

The CLI route additionally constrains responses with `config/pitch_expectation_output_schema.json`. Its SHA-256 is recorded in every CLI pass manifest and checked across all three passes at consensus time. A first unconstrained attempt generated only A/B: Sol returned an empty `reasoning_basis`, violating the schema; this incomplete attempt is retained locally under `artifacts/pitch_expectations/attempt_1/`. A subsequent six-source run was archived under `attempt_2/` when the generated worksheet revealed a source title disclosing a prior series result. The title was quarantined, the input manifest changed, and **all three** passes were restarted for the corrected five-source set with identical rubric and response schema. No row was selectively retried or assessment value retained from either superseded run.

```bash
: "${RUN_TAG:?choose a fresh local run tag; never overwrite earlier passes}"
SCREEN="artifacts/pitch_expectations/source_candidates_${RUN_TAG}.jsonl"
CAPTURES="data/interim/pitch_expectation_captures_${RUN_TAG}"
RUN_DIR="artifacts/pitch_expectations/${RUN_TAG}"
python3.11 scripts/collect_pitch_expectation_candidates.py --output "$SCREEN" --retry-transient
python3.11 scripts/materialize_pitch_expectation_source_statuses.py --candidates "$SCREEN" --captures "$CAPTURES"
# Independently review each pre_match_candidate; write captures or conservative dispositions.
python3.11 scripts/build_pitch_expectation_inputs.py --screened-candidates "$SCREEN" --captures "$CAPTURES" --output "$RUN_DIR/inputs.jsonl" --manifest "$RUN_DIR/input_manifest.json"
python3.11 scripts/audit_pitch_expectations.py --inputs "$RUN_DIR/inputs.jsonl" --manifest "$RUN_DIR/input_manifest.json" --output "$RUN_DIR/leakage_audit.json"
python3.11 scripts/run_pitch_expectation_agents_codex.py --assessor A --model gpt-5.6-luna --run-id "$RUN_ID_A" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/run_pitch_expectation_agents_codex.py --assessor B --model gpt-5.6-luna --run-id "$RUN_ID_B" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/run_pitch_expectation_agents_codex.py --assessor C --model gpt-6-sol --run-id "$RUN_ID_C" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/build_pitch_expectation_consensus.py --input-dir "$RUN_DIR" --consensus-output "data/processed/pitch_expectation_consensus_${RUN_TAG}.csv" --agreement-output "$RUN_DIR/agreement.json" --worksheet-output "$RUN_DIR/human_audit.csv"
```

The original five-source run remains locally preserved but is **superseded**, not part of the current measurement release. Its page parser missed some focal article bodies, and revised screening changed the eligibility of two previously assessed sources; none of its assessments was selectively carried forward. The outcome-blind `attempt_4` re-screen covered all 227 timing-eligible registry candidates (plus two excluded for ambiguous timing). Independent excerpt review retained **27 assessable sources**, with 67 contaminated/ambiguous, 132 needing further review, and one unavailable. The 27 include 21 development and six 2025–26 locked-source records, spread across seven source providers; **none** is from 2024 validation. Source review used only screened excerpts and provenance, not old pitch labels or outcomes. Rights-sensitive snapshots, captures, assessor passes, and generated tables remain ignored by Git and require separate rights review before publication.

The Responses API route remains available separately:

```bash
# Use the same frozen screened inputs and run directory, but a separate fresh run tag.
python3.11 scripts/run_pitch_expectation_agents.py --assessor A --model "$LUNA_MODEL_ID" --reasoning-effort high --run-id "$RUN_ID_A" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/run_pitch_expectation_agents.py --assessor B --model "$LUNA_MODEL_ID" --reasoning-effort high --run-id "$RUN_ID_B" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/run_pitch_expectation_agents.py --assessor C --model "$SOL_MODEL_ID" --reasoning-effort high --run-id "$RUN_ID_C" --inputs "$RUN_DIR/inputs.jsonl" --input-manifest "$RUN_DIR/input_manifest.json" --output-dir "$RUN_DIR"
python3.11 scripts/build_pitch_expectation_consensus.py --input-dir "$RUN_DIR" --consensus-output "data/processed/pitch_expectation_consensus_${RUN_TAG}.csv" --agreement-output "$RUN_DIR/agreement.json" --worksheet-output "$RUN_DIR/human_audit.csv"
```

Set `OPENAI_API_KEY`, `LUNA_MODEL_ID`, `SOL_MODEL_ID`, `RUN_TAG`, and distinct `RUN_ID_A`, `RUN_ID_B`, `RUN_ID_C` to real available values before using the API route; CLI runs do not need the API key. Never mix separate run directories. Complete, hashed A/B/C passes are required before consensus. Majority is calculated **separately for each categorical field**; three-way disagreements yield `uncertain`; median confidence and the four gates are deterministic. A source with no safe original content is not assessed. The versioned `agreement.json` reports per-field and pairwise exact agreement, Cohen's kappa only when defined, distributions by year/provider/competition/split, and sparse category cells. These measure **model-assessment stability**, not true pitch accuracy or human intercoder reliability. The versioned `human_audit.csv` selects up to 15 varied cases; human ratings and notes remain blank until independently completed.

The frozen Cricsheet raw snapshot and generated model table are absent in the fresh clone; source metadata counts must not be presented as independently reproduced modern cohort or paired innings totals. The consensus report marks `cohort_pairing_verified=false`; verify cohort pairing from the snapshot after approval, without opening locked outcomes.

Measurement-only diagnostic for `attempt_4`: among 27 consensus reports the overall expected-environment categories are 13 `batting_favorable`, four `pace_seam_favorable`, three `spin_slow_favorable`, one `balanced`, and six `uncertain`. Overall-category agreement is 3/3 on 23 and 2/3 on four; eight reports have all-fields unanimity. Development comprises 21 sources, with only ten primary-eligible batting-favorable and two primary-eligible pace/seam-favorable cases; the other development categories are smaller still. Six records are from the locked-source subgroup, but **no locked outcomes were opened or scored**. No 2024 validation source passed review. The 15-case human worksheet is **unrated**. These are measurements of assessed source text, not pitch truth, human reliability, a paired-cohort estimate, or an outcome association.

**Stop before outcome modeling.** Category variation now exists, but this selected 27-source set remains too sparse for a defensible multi-category pitch interaction and lacks 2024 validation, verified cohort pairing, and a completed human sanity audit. Classify current viability `PITCH_EXPLORATORY_ONLY`: do not fit or claim a new pitch/outcome model. The historical `run_pitch_interaction_analysis.py` remains legacy provenance, not a substitute. Full-cohort results are unchanged. Any expectation-specific model table, associations, 2024 evaluation, figures, or abstract claim need documented measurement review and explicit approval; every manifest retains `locked_test_scored=false`.
