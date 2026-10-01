# Documentation Map

This page separates the **current SSAC27 submission evidence** from supporting methodology, historical work, and the separate pitch-measurement track. It is intended to make the repository easy to review without changing any underlying research content.

## Start here — current SSAC27 submission

- [`ssac27_abstract_final.md`](ssac27_abstract_final.md) — final submission-ready abstract.
- [`ssac27_submission_source_of_truth.md`](ssac27_submission_source_of_truth.md) — authoritative current title, research question, claim boundary, Figure 1/Table 1 inputs, and evidence navigation.
- [`ssac27_numeric_handoff.md`](ssac27_numeric_handoff.md) — verified corrected numbers, uncertainty, limitations, hashes, and reproduction commands.
- [`ssac27_data_availability.md`](ssac27_data_availability.md) — exact public data source, frozen archive hash, cohort selection, and reproduction path.
- [`ssac27_submission_checklist.md`](ssac27_submission_checklist.md) — final submission fields, claim guardrails, and portal checks.
- [`ssac27_manuscript_structure.md`](ssac27_manuscript_structure.md) — Sloan-style full-manuscript organization built from the existing research.
- [`research_question_and_introduction.md`](research_question_and_introduction.md) — current title, question, introduction, and claim boundary.
- [`results.md`](results.md) — current corrected result narrative at the top; older results are explicitly marked superseded.

## Frozen methods and validation

- [`ssac27_powerplay_tradeoff_protocol.md`](ssac27_powerplay_tradeoff_protocol.md) — frozen estimand, context grid, support rules, and analysis protocol.
- [`ssac27_tradeoff_statistical_spec.md`](ssac27_tradeoff_statistical_spec.md) — statistical model, uncertainty, comparisons, and reporting rules.
- [`ssac27_tradeoff_data_audit.md`](ssac27_tradeoff_data_audit.md) — amended-source cohort and extraction audit.
- [`research_design.md`](research_design.md) — broader research design and leakage controls.
- [`data_dictionary.md`](data_dictionary.md) — exact row-level fields and definitions.
- [`limitations.md`](limitations.md) — interpretation, rights, and external constraints.
- [`literature/ssac27_powerplay_tradeoff_prior_art.md`](literature/ssac27_powerplay_tradeoff_prior_art.md) — prior-art review for the current tradeoff question.

## Reproducibility and provenance

- [`transformation_log.md`](transformation_log.md) — transformation and audit trail.
- [`sources.md`](sources.md) — data/source provenance.
- [`execution_roadmap.md`](execution_roadmap.md) — build and milestone roadmap.
- `../artifacts/abstract/ssac27_evidence.json` — tracked aggregate evidence.
- `../artifacts/abstract/ssac27_evidence_ledger.csv` — claim/evidence ledger.
- `../artifacts/abstract/ssac27_validation.json` — abstract validation artifact.

## Separate pitch-measurement work

These documents are **not part of the current SSAC27 run-wicket tradeoff result** unless explicitly stated otherwise.

- [`pitch_expectation_method.md`](pitch_expectation_method.md) — new outcome-blind pre-match expectation measurement design.
- [`pitch_collection_status.md`](pitch_collection_status.md) — source collection coverage/status.
- [`pitch_codebook.md`](pitch_codebook.md) — historical explicit-source pitch coding.
- [`pitch_source_expansion_pe008.md`](pitch_source_expansion_pe008.md) — source expansion work.

Pitch is excluded from the current corrected tradeoff analysis.

## Historical / superseded planning and results

These files are preserved for provenance and should not be read as the current submission claim set:

- [`paper_outline.md`](paper_outline.md) — contains the current direction at the top but retains the older pitch-centered manuscript plan below for archival continuity.
- [`ssac27_submission_plan.md`](ssac27_submission_plan.md) — earlier submission planning.
- [`ssac27_pre_reliability_prep_report.md`](ssac27_pre_reliability_prep_report.md) — superseded pre-reliability preparation.
- [`modeling_status.md`](modeling_status.md) — broader modeling history/status, including preliminary work.
- [`archive/README_pre_sloan_restructure_2026-09-30.md`](archive/README_pre_sloan_restructure_2026-09-30.md) — exact repository front-page README before the Sloan-style restructure.

## Reading order for an external reviewer

For the shortest complete path:

```text
README
  ↓
SSAC27 abstract
  ↓
submission source of truth
  ↓
verified numerical handoff
  ↓
statistical specification + data audit
  ↓
results
  ↓
reproduction commands / code / tests
```

This keeps the headline research question, actual results, validity checks, and reproducibility path visible before the historical and secondary material.
