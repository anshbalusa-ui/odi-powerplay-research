# What Makes a Successful ODI Powerplay?

[![Tests](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml/badge.svg)](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml)

Reproducible Python research pipeline for an **associational** study of which first-10-over ODI batting profiles are linked to winning, how much they add beyond opposition strength and match context, and whether those relationships vary by **source-stated pre-match pitch behavior**.

## Research scope

The primary cohort is **all clean men's ODIs from 2015 through the fixed Cricsheet snapshot**, regardless of competition type. It includes bilateral series, World Cups, Champions Trophies, continental cups, multi-team series, and qualification pathways. It does not mix Tests or T20s into the analysis.

World Cups are a labeled subgroup and sensitivity analysis, not the main dataset. A broader historical ODI cohort can be used as a second sensitivity analysis with explicit era controls; it is not silently pooled into the modern primary analysis.

## Two-track deliverables

- **SSAC27 milestone:** finish a results-complete, reproducible analysis from the broad modern-ODI cohort for the abstract deadline on October 1, 2026 at 11:59 p.m. ET. The submission is a milestone, not the endpoint of the research.
- **Full research paper:** continue expanding the cohort, source-stated pitch-effect coding, robustness analyses, and paper after the SSAC abstract is submitted, regardless of the competition decision.

The SSAC version will emphasize one applied question: what makes a successful ODI powerplay, and when does the best balance of aggression and wicket preservation change? The full cohort estimates powerplay-outcome associations; the verified-pitch-report subset is a prespecified effect-modification analysis within that same question. See `docs/ssac27_submission_plan.md`.

## Primary research question

> Among men's One Day International cricket matches, how are powerplay runs, wickets lost, boundary percentage, and dot-ball percentage associated with the batting team's probability of winning after accounting for pre-match opposition strength, innings order, toss, venue, year, and competition type—and, within the verified-pitch-report subgroup, how do those associations vary by **pitch effects explicitly stated in eligible pre-match sources**?

The wording is intentionally **associated with**, not **causes**. This is observational data.

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
                                      \
eligible pre-match source-stated pitch effects -> audited merge -> leakage-safe model table

model table -> chronological splits -> logistic/RF/XGBoost -> calibration/CI/plots
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

Generated primary/cohort datasets are ignored by Git and reproduced from the
checksummed raw snapshot. The tracked hand-audit and pitch-queue templates contain
no source prose and no secret data.

## Source-stated pitch-effect data and analysis

The **current rule** is strict: each accepted pre-match report may populate analytical pitch fields only from **playing effects explicitly stated by that source**. The intended fields are one primary category (`batting_friendly`, `balanced`, `pace_seam`, `spin`, `slow_two_paced`, or `unknown`) plus explicitly stated batting-ease, pace/seam-support, spin-support, bounce, two-paced, and dew expectations.

**The project performs zero independent pitch diagnosis.** Physical descriptions such as dry, dusty, grassy, green, moist, hard, cracked, worn, tacky, or used may be retained in the short provenance paraphrase, but they are never converted by the researcher into pitch-effect variables. For example, `dry` does not become `spin`, and `grass` does not become `pace_seam`, unless the eligible pre-match source itself explicitly states that expected playing effect. If the source does not state the effect, the corresponding field remains blank or `unknown`.

### Expanded 243-report release: re-audit complete

The auditable input file contains 243 source- and timing-verified reports. The
first 228 were coded under an earlier codebook; the 15 batch-24 rows were coded
under the current rule. Every legacy row now has a recorded disposition in
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

The current blinded assignment is the 46-row
`data/manual/pitch_reliability_sample_template.csv`, a deterministic 20% sample
of the 229-row compliant reference set. It retains source documents and match
identity but omits every first-coder pitch judgment. A genuinely independent
human second coder, reconciliation, and reliability report remain outstanding;
the repository tracks that blocker in issue #3.

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

The strict source-stated pitch-effect analysis is now materialized from the
229-row compliant release; its 14 source-unavailable legacy rows are excluded.
Independent double-coding and reconciliation remain incomplete. The
2025–2026 locked-test outcomes remain unscored.

Do not automate bulk collection from ESPNcricinfo under the terms reviewed for
this project. ESPN live commentary and post-match reporting are ineligible because
they disclose match information unavailable at the prediction timestamp. Use only
documented pre-match evidence, retain provenance and short original paraphrases,
and report source coverage across years, venues, competition types, and outcomes.

## Reproducibility rules

- Never modify raw files after download; use dated/checksummed source manifests.
- Keep original pitch-report URLs and short paraphrased notes alongside effect codes.
- Never infer a pitch effect from a physical surface descriptor that the source did not explicitly connect to that effect.
- The completed legacy re-audit is recorded in `data/manual/pitch_code_reaudit.csv`;
  source-unavailable rows stay excluded and any future rows must follow the current rule.
- Version the pitch-effect codebook before double-coding begins.
- Derive team strength using only matches before the focal match date.
- Keep both rows from a match in the same split/fold.
- Fit preprocessing inside each training fold.
- Lock the final test period until analysis choices are frozen.
- Save exclusions, join failures, package versions, random seeds, model parameters, predictions, and figures.

## Key documents

- `AGENTS.md` — non-negotiable agent/coder rules, including explicit-source-only pitch coding
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
