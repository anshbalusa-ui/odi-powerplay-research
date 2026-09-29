# What Makes a Successful ODI Powerplay?

[![Tests](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml/badge.svg)](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml)

Reproducible Python research pipeline for an **associational** study of first-10-over ODI batting profiles, winning, and effect modification by **model-estimated pre-match expected playing conditions**. Historical explicit-source-only effects remain separately preserved.

## Research scope

The primary cohort is **all clean men's ODIs from 2015 through the fixed Cricsheet snapshot**, regardless of competition type. It includes bilateral series, World Cups, Champions Trophies, continental cups, multi-team series, and qualification pathways. It does not mix Tests or T20s into the analysis.

World Cups are a labeled subgroup and sensitivity analysis, not the main dataset. A broader historical ODI cohort can be used as a second sensitivity analysis with explicit era controls; it is not silently pooled into the modern primary analysis.

## Two-track deliverables

- **SSAC27 milestone:** finish a results-complete, reproducible analysis from the broad modern-ODI cohort for the abstract deadline on October 1, 2026 at 11:59 p.m. ET. The submission is a milestone, not the endpoint of the research.
- **Full research paper:** continue expanding the cohort, separately audited pre-match expectation measurement, robustness analyses, and paper after the SSAC abstract is submitted, regardless of the competition decision.

The SSAC version will emphasize one applied question: what makes a successful ODI powerplay, and when does the best balance of aggression and wicket preservation change? The full cohort estimates powerplay-outcome associations; the verified-pitch-report subset is a prespecified effect-modification analysis within that same question. See `docs/ssac27_submission_plan.md`.

## Primary research question

> Among men's One Day International cricket matches, how are powerplay runs, wickets lost, boundary percentage, and dot-ball percentage associated with the batting team's probability of winning after accounting for pre-match opposition strength, innings order, toss, venue, year, and competition type—and, within the verified-pitch-report subgroup, how do those associations vary by **model-estimated pre-match expected playing conditions**?

The wording is intentionally **associated with**, not **causes**. This is observational data.

The new pitch-expectation measurement is **not yet an effect-modification
result**. The hardened outcome-blind source screen has 30 independently
reviewed excerpts (26 live originals, four pre-start archived originals),
including three 2024 validation reports. Earlier 27-row assessor passes are
superseded; the revised 30-row input release has not been assessed. Fresh
passes require provider-observed response model IDs; the available CLI exposes
only requested routes, and no API credential is configured locally. The human
evidence audit remains unrated. No new pitch/outcome interaction has been run
or approved. See `docs/pitch_expectation_method.md` for source exclusions
and the separate historical pitch release.

## Unit of analysis

One row represents one batting-team innings in one match. The outcome is `batting_team_won`. A match normally contributes two rows, so resampling, confidence intervals, and cross-validation must group by `match_id`.

## What is already implemented

- A standard-library Cricsheet JSON extractor for first-10-over runs, wickets,
  run rate, boundary-ball percentage, dot-ball percentage, match context, and outcome.
- Definitions and regression tests for legal deliveries, dots, boundaries, wickets
  lost, incomplete powerplays, ties/no-results, and super overs.
- A secure Cricsheet ODI downloader that records the URL, retrieval time, and SHA-256 checksum.
- An auditable cleaning stage separating raw innings, retained matches, exclusions,
  the broad 2015-forward primary cohort, and competition-type subgroups.
- A full-cohort metric audit covering formulas, ranges, match pairing, and outcome labels.
- A deterministic 20-match raw-JSON re-extraction audit covering 1,120 field-level
  comparisons across 40 innings with zero discrepancies.
- Date-batched pre-match Elo and rolling prior-20 win rates computed from all
  available clean history without same-day or future leakage.
- Date-batched prior-20 venue powerplay histories covering 997 of 1,094 primary
  matches without using same-day or future performances.
- A hashed, feature-allowlisted model table with development (through 2023),
  temporal-validation (2024), and locked-test (2025+) partitions.
- Fixed nested logistic models, constrained Random Forest and XGBoost challengers,
  rolling-origin diagnostics, calibration estimates, and 2,000-repetition
  whole-match bootstrap confidence intervals.
- A deterministic 24-innings hand-audit worksheet spanning every year from 2015–2026.
- An outcome-blind 1,094-match pitch-source queue plus validators, complete
  collection-status reporting, provider-concentration auditing, and a leakage-safe
  pitch-report/model-table merge.
- Rights-safe ESPN linkage candidates for all 1,094 queued matches, with explicit
  human-verification fields and a zero-network structural audit.
- A 1,094-match outcome-blind scheduled-start template with IANA-timezone,
  cohort-identity, provenance, and UTC-conversion validation.
- An expanded release of 243 timing-verified pre-match reports, 357 reviewed
  set-asides, and 494 explicitly unreviewed matches, with a completed
  explicit-source-only re-audit registry.
- A strict 229-row compliant pitch release excluding 14 source-unavailable rows,
  a 458-row pitch model table, and a deterministic blinded 46-match reliability
  sample template.
- Pitch/source-timing templates, research design, data dictionary, pitch-effect codebook,
  transformation log, paper outline, and execution roadmap.

For the Cricsheet snapshot retrieved on September 10, 2026, the pipeline found
3,182 matches, retained 2,742 in the core clean dataset, and selected 1,094 matches
(2,188 team-innings) for the 2015-forward men's ODI primary cohort. The World Cup
subgroup contains 110 matches; it is not the primary sample.

## Planned pipeline

```text
Cricsheet JSON -> match/innings table -> rolling team and venue history
verified pre-match source -> reviewed safe text -> 3 blind assessor passes
                                      -> mechanical expectation consensus
measurement audit + human worksheet -> human approval -> separate pitch model
```

## Quick start

Use Python 3.11. Dataset construction and audits use the standard library; model
training uses the pinned project dependencies. On macOS, XGBoost also requires
`brew install libomp`.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/download_cricsheet.py --output-dir data/raw/cricsheet
python scripts/extract_cricsheet.py \
  --input-dir data/raw/cricsheet \
  --output data/interim/powerplay_innings.csv
python scripts/build_clean_dataset.py
python scripts/build_team_strength.py
python scripts/build_venue_conditions.py
python scripts/build_compliant_pitch_release.py
python scripts/build_model_table.py \
  --pitch-input data/processed/pitch_reports_compliant.csv \
  --match-start-input data/manual/match_start_times_verified.csv
python scripts/audit_powerplay_metrics.py
python scripts/audit_extraction.py
python scripts/build_hand_audit_sample.py
python scripts/build_pitch_collection_queue.py
python scripts/build_match_start_queue.py
python scripts/audit_match_start_times.py
python scripts/audit_espn_linkage.py
python scripts/audit_pitch_reaudit.py
python scripts/select_pitch_batch.py --output data/manual/pitch_batch_working.csv
python scripts/build_pitch_reliability_sample.py \
  --input data/processed/pitch_reports_compliant.csv
.venv/bin/python scripts/train_models.py --fit-without-locked-test
.venv/bin/python scripts/evaluate_models.py
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/reproduce.py --skip-download
```

## SSAC27 pre-reliability preparation outputs

The current branch also materializes the abstract-ready, unlocked analysis
without opening the locked 2025+ outcomes:

- `scripts/audit_full_cohort_analysis.py` independently audits the 2015–2024
  cohort, metric invariants, match pairing, and non-pitch feature allowlist.
- `scripts/build_ssac_full_cohort_results.py` writes canonical validation model
  outputs; `scripts/build_powerplay_marginal_results.py` writes
  model-standardized runs/wickets contrasts with an observational guardrail.
- `scripts/diagnose_pitch_sparsity.py` reports historical strict pitch-code cells;
  it is not a diagnostic for the new expectation variables.
- `scripts/audit_pitch_reliability.py`,
  `scripts/reconcile_pitch_reliability.py` and
  `scripts/run_pitch_interaction_analysis.py` remain historical
  explicit-source/human-reconciliation tools. The incomplete 46-row human
  recoding is superseded **for the new construct**, not claimed as completed.
  The legacy runner cannot be used as the new expectation analysis.
- `scripts/build_ssac_abstract_support.py` and
  `scripts/validate_ssac_abstract.py` build and validate the evidence-backed
  `docs/ssac27_abstract_skeleton.md` under the 499-word SSAC limit.

Generated tables and figures are intentionally ignored by Git; tracked abstract
evidence carries source hashes in its manifest. The public-repository audit still
requires a separate source-license/terms review for tracked pitch provenance.


Generated primary/cohort datasets are ignored by Git and reproduced from the
checksummed raw snapshot. The tracked hand-audit and pitch-queue templates contain
no source prose and no secret data.

## New pre-match expectation measurement

See [`docs/pitch_expectation_method.md`](docs/pitch_expectation_method.md).
`config/pitch_expectation_agent.json` freezes the allowed categorical expectation
variables, bounded inference, uncertainties, consensus and thresholds. Assessor
inputs are projected from verified pre-match metadata plus **newly retrieved,
independently reviewed original-source text**; old pitch codes, prior coder notes,
powerplay/outcome data and post-match information are excluded. Three independent
passes and deterministic consensus precede a small human evidence audit. The new
method does **not** claim true pitch behavior or human intercoder reliability.
No new pitch interaction is interpreted before the measurement gate and approval.

## Historical source-stated pitch-effect data and analysis

The **historical rule** is strict: each accepted report populates legacy fields
only from playing effects explicitly stated by that source.

**The historical scheme performs zero independent pitch diagnosis.** Physical
descriptions such as dry or green are never converted into historical effect
fields. The new expectation scheme permits bounded, source-grounded inference;
its variables are distinct and cannot be mixed with these historical fields.

### Expanded 243-report release: re-audit complete

The auditable input file contains 243 source- and timing-verified reports. The
first 228 were coded under an earlier codebook; the 15 batch-24 rows were coded
under the then-current historical strict rule. Every legacy row now has a recorded disposition in
`data/manual/pitch_code_reaudit.csv`: 169 `passed_revised`, 45
`passed_unchanged`, and 14 `source_unavailable`, alongside 15
`current_standard` rows. The registry has zero validation issues.

The strict analytical release is
`data/processed/pitch_reports_compliant.csv`. It contains 229 rows: 214 accepted
legacy rows plus all 15 current-standard rows. The 14 source-unavailable rows
are omitted, not assigned replacement codes. Its compliant primary-category
counts are 104 `batting_friendly`, 33 `spin`, 29 `balanced`, 23 `unknown`, 22
`pace_seam`, and 18 `slow_two_paced`. The release summary and input/output
hashes are in `artifacts/tables/pitch_compliant_release.json`.

The release builder enforces the cutover: it validates the full registry and
refuses to build while any legacy row is `pending`. It retains only
source-stated expected playing effects. Physical descriptions such as dry,
dusty, grassy, green, moist, hard, cracked, worn, tacky, or used remain
provenance only; they are never converted by the researcher into pitch-effect
variables.

The compliant pitch model table contains 458 paired team-innings from 229
matches: 336 development rows (168 matches), 20 validation rows (10 2024
matches), and 102 locked-test rows (51 matches). The locked partition is
reserved and unscored. The 2024 pitch-model output is a reproducibility and
sample-size checkpoint, not a reliability-cleared substantive claim.

Twenty-four outcome-blind pitch batches cover 600 reviewed matches: 243
non-ESPN pre-match reports passed source and timing validation, 357 reviewed
matches are listed in `data/manual/pitch_set_aside.csv`, and 494 remain
explicitly unreviewed. Verified source/timing coverage is 243/1,094
(22.212066%); the compliant analytical release is 229/1,094.

The historical blinded assignment is the 46-row
`data/manual/pitch_reliability_sample_template.csv`, a deterministic 20% sample
of the 229-row historical compliant reference set. Independent human second
coding/reconciliation was **not completed**. This requirement has been retired
for the new expectation construct; neither human kappa nor reconciliation
is fabricated.

The minimized tracked releases are `data/manual/pitch_reports_verified.csv`,
`data/manual/pitch_code_reaudit.csv`, and
`data/manual/match_start_times_verified.csv`. They contain provenance, factual
timestamps, original/re-audit codes, and short original paraphrases, not copied
article text. The derived compliant release is rebuilt from those inputs.

The 243 accepted reports span 35 normalized provider hostnames. MyKhel
contributes 59 matches (24.3%), ICC 36 (14.8%), and Business Standard 27
(11.1%); the three largest providers account for 50.2%, and the provider HHI is
1,131. This documents a multi-source measurement design rather than implying
that all pitch data came from ESPN or any single publisher. Provider diversity
does not remove source-specific wording or selection bias, so
`artifacts/tables/pitch_source_providers.csv` reports each provider's category
and confidence mix.


For continued coding, start with the tracked contributor template or select another
balanced batch, then copy completed rows into the ignored local
`data/manual/pitch_reports.csv`. Separately copy only corresponding match rows from
`data/manual/match_start_times_template.csv` into the ignored
`data/manual/match_start_times.csv`; matches without eligible pitch reports need no
timing work. Verify scheduled local starts from cited sources, record an IANA
timezone, convert to UTC, and audit the working subset before validating pitch rows.
Only rows with `start_time_status=verified` can establish that a pitch report
predated play. Start-time and source-provenance fields are audit metadata only:
they are never joined into the model table and are explicitly prohibited as
predictors.

The historical strict derivative has 229 rows after excluding the 14
source-unavailable legacy rows. The new model-estimated expectation release
must be built independently from freshly reviewed source captures; its
assessment coverage and category distributions cannot be inherited from those
legacy rows. The 2025–2026 locked-test outcomes remain unscored.

Do not automate bulk collection from ESPNcricinfo under the terms reviewed for
this project. ESPN live commentary and post-match reporting are ineligible because
they disclose match information unavailable at the prediction timestamp. Use only
documented pre-match evidence, retain provenance and short original paraphrases,
and report source coverage across years, providers, venues and competition types; assessors never receive outcome fields.

## Reproducibility rules

- Never modify raw files after download; use dated/checksummed source manifests.
- Keep original pitch-report URLs and short paraphrased notes with the
  **historical** effect codes, never inside the new assessor payload.
- Apply the no-inference rule only to the historical explicit-source derivative;
  the distinct new expectation rubric permits bounded source-grounded inference.
- Preserve the completed historical re-audit in
  `data/manual/pitch_code_reaudit.csv`; exclude its 14 source-unavailable rows.
- Version and hash the new rubric before any blinded three-pass assessment;
  a rubric change invalidates all prior new-method passes.
- Derive team strength using only matches before the focal match date.
- Keep both rows from a match in the same split/fold.
- Fit preprocessing inside each training fold.
- Lock the final test period until analysis choices are frozen.
- Save exclusions, join failures, package versions, random seeds, model parameters, predictions, and figures.

## Key documents

- `AGENTS.md` — historical explicit-source and distinct new expectation policies
- `docs/research_design.md` — hypotheses, cohort, leakage rules, modeling, evaluation, and robustness checks
- `docs/results.md` — preliminary cohort, powerplay, and 2024 validation findings
- `docs/limitations.md` — interpretation boundaries, data constraints, and external blockers
- `docs/research_question_and_introduction.md` — final working title, research question, and paper introduction
- `docs/data_dictionary.md` — row-level schema and exact definitions
- `docs/pitch_collection_status.md` — outcome-blind pitch-source collection progress and batch audit
- `docs/modeling_status.md` — exact preliminary model specifications, split counts, validation results, and lock state
- `docs/pitch_codebook.md` — reproducible rules for standardizing explicitly stated pre-match pitch effects
- `docs/transformation_log.md` — every planned transformation and audit artifact
- `docs/execution_roadmap.md` — the build order and milestone checklist
- `docs/paper_outline.md` — section-by-section paper structure
- `docs/ssac27_submission_plan.md` — focused deadline, abstract requirements, and sprint scope

## Data-source attribution

Match data: one fixed, checksummed Cricsheet JSON archive. The auditable pitch
input contains 243 individually cited non-ESPN pre-match reports from 35
normalized provider hostnames. Its strict derivative contains 229 rows after
excluding 14 source-unavailable legacy reports; every retained effect is
explicitly stated by an eligible source. ESPN candidates are retained only for
human/licensed follow-up; no ESPN page text or live/post-match commentary is in
the released pitch codes. Generic hourly weather variables are not part of the
primary design. Follow each source's licence/terms and inspect
`artifacts/tables/pitch_compliant_release.json` for release hashes.

## Licence

The original code and documentation in this repository are released under the MIT Licence. Third-party data and report content remain governed by their respective licences and terms; the MIT Licence does not relicense them.
