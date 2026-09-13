# What Makes a Successful ODI Powerplay?

[![Tests](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml/badge.svg)](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml)

Reproducible Python research pipeline for an **associational** study of which first-10-over ODI batting profiles are linked to winning, how much they add beyond opposition strength and match context, and whether those relationships vary by verified pre-match pitch type.

## Research scope

The primary cohort is **all clean men's ODIs from 2015 through the fixed Cricsheet snapshot**, regardless of competition type. It includes bilateral series, World Cups, Champions Trophies, continental cups, multi-team series, and qualification pathways. It does not mix Tests or T20s into the analysis.

World Cups are a labeled subgroup and sensitivity analysis, not the main dataset. A broader historical ODI cohort can be used as a second sensitivity analysis with explicit era controls; it is not silently pooled into the modern primary analysis.

## Two-track deliverables

- **SSAC27 milestone:** finish a results-complete, reproducible analysis from the broad modern-ODI cohort for the abstract deadline on October 1, 2026 at 11:59 p.m. ET. The submission is a milestone, not the endpoint of the research.
- **Full research paper:** continue expanding the cohort, pitch coding, robustness analyses, and paper after the SSAC abstract is submitted, regardless of the competition decision.

The SSAC version will emphasize one applied question: what makes a successful ODI powerplay, and when does the best balance of aggression and wicket preservation change? The full cohort estimates powerplay-outcome associations; the verified-pitch subset is a prespecified effect-modification analysis within that same question. See `docs/ssac27_submission_plan.md`.

## Primary research question

> Among men's One Day International cricket matches, how are powerplay aggression and wicket preservation associated with the batting team's probability of winning after accounting for pre-match team strength, innings order, toss, venue, year, and competition type—and, within the verified-pitch subgroup, how do those associations vary by pitch conditions?

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
  pitch/model-table merge.
- Rights-safe ESPN linkage candidates for all 1,094 queued matches, with explicit
  human-verification fields and a zero-network structural audit.
- A 1,094-match outcome-blind scheduled-start template with IANA-timezone,
  cohort-identity, provenance, and UTC-conversion validation.
- An expanded release of 228 timing-verified provisional pitch codes, 347
  reviewed set-asides, and 519 explicitly unreviewed matches.
- Pitch/source-timing templates, research design, data dictionary, pitch codebook,
  transformation log, paper outline, and execution roadmap.

For the Cricsheet snapshot retrieved on September 10, 2026, the pipeline found
3,182 matches, retained 2,742 in the core clean dataset, and selected 1,094 matches
(2,188 team-innings) for the 2015-forward men's ODI primary cohort. The World Cup
subgroup contains 110 matches; it is not the primary sample.

## Planned pipeline

```text
Cricsheet JSON -> match/innings table -> rolling team and venue history
                                      \
pre-match pitch coding ---------------> audited merge -> leakage-safe model table

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
python scripts/build_model_table.py
python scripts/audit_powerplay_metrics.py
python scripts/build_hand_audit_sample.py
python scripts/build_pitch_collection_queue.py
python scripts/build_match_start_queue.py
python scripts/audit_match_start_times.py
python scripts/audit_espn_linkage.py
python scripts/select_pitch_batch.py --output data/manual/pitch_batch_working.csv
python scripts/build_pitch_reliability_sample.py
.venv/bin/python scripts/train_models.py --fit-without-locked-test
.venv/bin/python scripts/evaluate_models.py
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/reproduce.py --skip-download
```

Generated primary/cohort datasets are ignored by Git and reproduced from the
checksummed raw snapshot. The tracked hand-audit and pitch-queue templates contain
no source prose and no secret data.

Twenty-three outcome-blind pitch batches cover 575 reviewed matches: 228 non-ESPN
pre-match reports passed source and timing validation, 347 reviewed matches are
listed in `data/manual/pitch_set_aside.csv`, and 519 remain explicitly unreviewed.
Verified coverage is 228/1,094 (20.840951%). The prespecified 200-match collection
target is exceeded, but the codes remain provisional until at least 46 reports are
recoded by a genuinely independent coder. The blinded 46-row assignment is
`data/manual/pitch_reliability_sample_template.csv`; it retains source documents
and match identity but omits every first-coder pitch judgment. The minimized tracked
releases are `data/manual/pitch_reports_verified.csv` and
`data/manual/match_start_times_verified.csv`; they contain provenance, factual
timestamps, derived codes, and short original paraphrases, not copied article text.

The 228 accepted sources span 35 normalized provider hostnames. MyKhel contributes
53 matches (23.2%), ICC 36 (15.8%), and Business Standard 26 (11.4%); the top
three account for 50.4%, and the provider HHI is 1,132. This documents a
multi-source measurement design rather than implying that all pitch data came from
ESPN or any single publisher. Provider diversity does not remove source-specific
wording or selection bias, so `artifacts/tables/pitch_source_providers.csv` reports
each provider's category and confidence mix.

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
predictors. Reproduce the tracked audits and 228-match merge with:

```bash
.venv/bin/python scripts/audit_match_start_times.py \
  --input data/manual/match_start_times_verified.csv
.venv/bin/python scripts/audit_pitch_collection.py \
  --pitch-input data/manual/pitch_reports_verified.csv \
  --match-start-input data/manual/match_start_times_verified.csv
.venv/bin/python scripts/audit_pitch_sources.py
.venv/bin/python scripts/build_pitch_reliability_sample.py
.venv/bin/python scripts/build_model_table.py \
  --pitch-input data/manual/pitch_reports_verified.csv \
  --match-start-input data/manual/match_start_times_verified.csv
```

The pitch-adjusted analysis remains provisional: only ten verified-pitch matches
fall in the 2024 temporal-validation year, and independent double-coding is still
required. The 2025–2026 locked-test outcomes remain unscored.

Do not automate bulk collection from ESPNcricinfo under the terms reviewed for
this project. ESPN live commentary and post-match reporting are ineligible because
they disclose match information unavailable at the prediction timestamp. Use only
documented pre-match evidence, retain provenance and short original paraphrases,
and report source coverage across years, venues, competition types, and outcomes.

## Reproducibility rules

- Never modify raw files after download; use dated/checksummed source manifests.
- Keep original pitch-report URLs and short paraphrased notes alongside coded values.
- Version the pitch codebook before double-coding begins.
- Derive team strength using only matches before the focal match date.
- Keep both rows from a match in the same split/fold.
- Fit preprocessing inside each training fold.
- Lock the final test period until analysis choices are frozen.
- Save exclusions, join failures, package versions, random seeds, model parameters, predictions, and figures.

## Key documents

- `docs/research_design.md` — hypotheses, cohort, leakage rules, modeling, evaluation, and robustness checks
- `docs/results.md` — preliminary cohort, powerplay, and 2024 validation findings
- `docs/limitations.md` — interpretation boundaries, data constraints, and external blockers
- `docs/research_question_and_introduction.md` — final working title, research question, and paper introduction
- `docs/data_dictionary.md` — row-level schema and exact definitions
- `docs/pitch_collection_status.md` — outcome-blind pitch-source collection progress and batch audit
- `docs/modeling_status.md` — exact preliminary model specifications, split counts, validation results, and lock state
- `docs/pitch_codebook.md` — reproducible text-to-category rules
- `docs/transformation_log.md` — every planned transformation and audit artifact
- `docs/execution_roadmap.md` — the build order and milestone checklist
- `docs/paper_outline.md` — section-by-section paper structure
- `docs/ssac27_submission_plan.md` — focused deadline, abstract requirements, and sprint scope

## Data-source attribution

Match data: one fixed, checksummed Cricsheet JSON archive. Pitch conditions: 228
individually cited non-ESPN pre-match pitch/conditions reports from 35 normalized
provider hostnames. ESPN candidates are retained only for human/licensed follow-up;
no ESPN page text or live/post-match commentary is in the released pitch codes.
Generic hourly weather variables are not part of the primary design. Follow each
source's licence/terms and include a source statement in the final paper.

## Licence

The original code and documentation in this repository are released under the MIT Licence. Third-party data and report content remain governed by their respective licences and terms; the MIT Licence does not relicense them.
