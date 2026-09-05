# ODI Powerplay, Conditions, and Match Outcomes

[![Tests](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml/badge.svg)](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml)

Reproducible Python research pipeline for an **associational** study of how first-10-over ODI batting performance relates to the batting team's probability of winning under different pitch, weather, and match conditions.

## Recommended research scope

Start with a defensible pilot before attempting every ODI:

1. **Pilot:** men's ODI World Cups in 2015, 2019, and 2023.
2. **Chronological evaluation:** train/tune on 2015 and 2019; lock 2023 as the final test set.
3. **Expansion:** add other ODIs only after the pitch-report matching and leakage audit work reliably.

This scope spans Australia/New Zealand, England/Wales, and India; produces substantial variation in venue and conditions; and keeps manual pitch coding feasible. The pipeline itself is not tied to this scope.

## Two-track deliverables

- **SSAC27 milestone:** finish a focused, results-complete World Cup pilot for the abstract deadline on October 1, 2026 at 11:59 p.m. ET. The submission is a milestone, not the endpoint of the research.
- **Full research paper:** continue expanding the cohort, condition coding, robustness analyses, and paper after the SSAC abstract is submitted, regardless of the competition decision.

The SSAC version will emphasize one applied contribution: a conditions-adjusted assessment of whether an ODI powerplay was genuinely strong given wickets, opposition strength, pitch, weather, and innings order. See `docs/ssac27_submission_plan.md`.

## Primary research question

> How do runs and wickets in the first 10 overs of an ODI relate to the batting team's eventual win probability, and how does that relationship vary with pre-match pitch characteristics and early-match weather?

The wording is intentionally **relates to**, not **causes**. This is observational data.

## Unit of analysis

One row represents one batting-team innings in one match. The outcome is `batting_team_won`. A match normally contributes two rows, so resampling, confidence intervals, and cross-validation must group by `match_id`.

## What is already implemented

- A standard-library Cricsheet JSON extractor for first-10-over runs, wickets, run rate, boundary-ball percentage, dot-ball percentage, match context, and outcome.
- Definitions for legal deliveries, dots, boundaries, wickets lost, incomplete powerplays, ties/no-results, and super overs.
- A secure Cricsheet ODI downloader that records the URL, retrieval time, and SHA-256 checksum.
- An auditable cleaning stage that separates raw data, all extracted innings, retained matches, exclusions, and the World Cup pilot cohort.
- Human-audited pitch and match-start-time templates.
- A research design, data dictionary, pitch codebook, transformation log, paper outline, and staged execution roadmap.
- Tests using a small synthetic ODI fixture.

## Planned pipeline

```text
Cricsheet JSON -> match/innings table -> rolling pre-match team strength
                                      \
pre-match pitch coding ---------------> audited merge -> leakage-safe model table
                                      /
Open-Meteo hourly raw -> start-time weather features

model table -> chronological splits -> logistic/RF/XGBoost -> calibration/CI/SHAP/plots
```

## Quick start

Use Python 3.11. The extraction smoke test has no third-party runtime dependency.

```bash
python -m unittest discover -s tests -v
python scripts/download_cricsheet.py --output-dir data/raw/cricsheet
python scripts/extract_cricsheet.py \
  --input-dir data/raw/cricsheet \
  --output data/interim/powerplay_innings.csv
python scripts/build_clean_dataset.py
```

Then copy and complete:

- `data/manual/pitch_reports_template.csv`
- `data/manual/match_start_times_template.csv`
- `data/manual/venue_coordinates_template.csv`

Do not automate bulk collection from ESPNcricinfo until its current terms and access rules have been reviewed. For this project, manually coding the smaller World Cup pilot is transparent, auditable, and academically stronger than an opaque scraper.

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
- `docs/data_dictionary.md` — row-level schema and exact definitions
- `docs/pitch_codebook.md` — reproducible text-to-category rules
- `docs/transformation_log.md` — every planned transformation and audit artifact
- `docs/execution_roadmap.md` — the build order and milestone checklist
- `docs/paper_outline.md` — section-by-section paper structure
- `docs/ssac27_submission_plan.md` — focused deadline, abstract requirements, and sprint scope

## Data-source attribution

Match data: Cricsheet JSON. Weather data: Open-Meteo Historical Weather API. Pitch-report metadata: individually cited pre-match ESPNcricinfo reports. Follow the source licences/terms and include a source statement in the final paper.

## Licence

The original code and documentation in this repository are released under the MIT Licence. Third-party data and report content remain governed by their respective licences and terms; the MIT Licence does not relicense them.
