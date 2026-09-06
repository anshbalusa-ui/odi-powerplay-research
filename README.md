# ODI Powerplay, Pitch Conditions, and Match Outcomes

[![Tests](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml/badge.svg)](https://github.com/anshbalusa-ui/odi-powerplay-research/actions/workflows/tests.yml)

Reproducible Python research pipeline for an **associational** study of how first-10-over ODI batting performance relates to the batting team's probability of winning on different types of pitches.

## Research scope

The primary cohort is **all clean men's ODIs from 2015 through the fixed Cricsheet snapshot**, regardless of competition type. It includes bilateral series, World Cups, Champions Trophies, continental cups, multi-team series, and qualification pathways. It does not mix Tests or T20s into the analysis.

World Cups are a labeled subgroup and sensitivity analysis, not the main dataset. A broader historical ODI cohort can be used as a second sensitivity analysis with explicit era controls; it is not silently pooled into the modern primary analysis.

## Two-track deliverables

- **SSAC27 milestone:** finish a results-complete, reproducible analysis from the broad modern-ODI cohort for the abstract deadline on October 1, 2026 at 11:59 p.m. ET. The submission is a milestone, not the endpoint of the research.
- **Full research paper:** continue expanding the cohort, pitch coding, robustness analyses, and paper after the SSAC abstract is submitted, regardless of the competition decision.

The SSAC version will emphasize one applied contribution: a pitch-adjusted assessment of whether an ODI powerplay was genuinely strong given wickets, pre-match team-strength difference, pitch behavior, and innings order. See `docs/ssac27_submission_plan.md`.

## Primary research question

> Among men's One Day International cricket matches, how are runs scored and wickets lost during the first 10 overs associated with the batting team's probability of winning after accounting for pre-match team-strength difference, innings order, toss, venue, year, and competition type—and how do these associations vary with pre-match pitch conditions such as batting ease, pace/seam assistance, spin assistance, bounce, and two-paced behavior?

The wording is intentionally **associated with**, not **causes**. This is observational data.

## Unit of analysis

One row represents one batting-team innings in one match. The outcome is `batting_team_won`. A match normally contributes two rows, so resampling, confidence intervals, and cross-validation must group by `match_id`.

## What is already implemented

- A standard-library Cricsheet JSON extractor for first-10-over runs, wickets, run rate, boundary-ball percentage, dot-ball percentage, match context, and outcome.
- Definitions for legal deliveries, dots, boundaries, wickets lost, incomplete powerplays, ties/no-results, and super overs.
- A secure Cricsheet ODI downloader that records the URL, retrieval time, and SHA-256 checksum.
- An auditable cleaning stage that separates raw data, all extracted innings, retained matches, exclusions, the broad 2015-forward primary cohort, and competition-type subgroups.
- Human-audited pitch and source-timing templates.
- A research design, data dictionary, pitch codebook, transformation log, paper outline, and staged execution roadmap.
- Tests using a small synthetic ODI fixture.

For the current checksummed Cricsheet snapshot, the cleaning pipeline found 3,178 matches, retained 2,739 in the core clean dataset, and selected 1,093 matches (2,186 team-innings) for the 2015-forward men's ODI primary cohort. The World Cup subgroup contains 110 of those matches; it is not the primary sample.

## Planned pipeline

```text
Cricsheet JSON -> match/innings table -> rolling pre-match team strength
                                      \
pre-match pitch coding ---------------> audited merge -> leakage-safe model table

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

The cleaning command creates `data/processed/powerplay_innings_primary.csv` for the main analysis and `data/processed/powerplay_innings_world_cup_subgroup.csv` only for subgroup checks. Generated datasets are ignored by Git and reproduced from the checksummed raw snapshot.

Then copy and complete:

- `data/manual/pitch_reports_template.csv`
- `data/manual/match_start_times_template.csv`
- `data/manual/venue_crosswalk_template.csv`

Do not automate bulk collection from ESPNcricinfo under the terms reviewed for this project. Use a documented, source-audited manual collection design and report pitch-source coverage across years, venues, competition types, and outcomes. Never replace a missing pre-match pitch report with a post-match description.

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
- `docs/research_question_and_introduction.md` — final working title, research question, and paper introduction
- `docs/data_dictionary.md` — row-level schema and exact definitions
- `docs/pitch_collection_status.md` — outcome-blind pitch-source collection progress and batch audit
- `docs/pitch_codebook.md` — reproducible text-to-category rules
- `docs/transformation_log.md` — every planned transformation and audit artifact
- `docs/execution_roadmap.md` — the build order and milestone checklist
- `docs/paper_outline.md` — section-by-section paper structure
- `docs/ssac27_submission_plan.md` — focused deadline, abstract requirements, and sprint scope

## Data-source attribution

Match data: Cricsheet JSON. Pitch conditions: individually cited, pre-match pitch/conditions reports, with ESPNcricinfo used where an eligible report is available. Generic hourly weather variables are not part of the primary design. Follow the source licences/terms and include a source statement in the final paper.

## Licence

The original code and documentation in this repository are released under the MIT Licence. Third-party data and report content remain governed by their respective licences and terms; the MIT Licence does not relicense them.
