# Complete ODI Powerplay Research Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a tested, leakage-safe, reproducible ODI research pipeline that joins Cricsheet first-10-over performance, pre-match team strength, and source-audited pitch conditions, then evaluates chronological logistic and nonlinear models.

**Architecture:** Treat the fixed Cricsheet snapshot as the immutable match foundation. Build small modules for validation, pre-match strength, pitch coding/merging, chronological splits, modeling, evaluation, and graphics; scripts turn those modules into saved CSV/JSON/PNG artifacts. Pitch collection remains outcome-blind and source-by-source, with models reported both for the full cohort without pitch and for the source-audited pitch subset.

**Tech Stack:** Python 3.12, standard-library CSV/JSON/hash tools, pandas, NumPy, scikit-learn, statsmodels, XGBoost, SHAP, matplotlib/seaborn, YAML, Git/GitHub.

**Spec:** `docs/research_design.md`

## Global Constraints

- Primary cohort is every clean men's ODI from 2015 through the fixed Cricsheet snapshot; World Cups are a subgroup only.
- The prediction timestamp is the end of the focal batting team's tenth over.
- Use Cricsheet delivery events for runs, wickets, legal balls, boundaries, and dots.
- Never use post-match reports, later-innings events, final totals, or future team results as predictors.
- Pitch evidence must be match-specific, published before play, and coded without inspecting the outcome.
- Do not bulk scrape ESPNcricinfo; retain direct URLs and short original paraphrases only.
- Keep both rows from one match in the same chronological split and bootstrap cluster.
- Locked test period is 2025-01-01 through the fixed 2026 snapshot and is scored only after model choices are frozen.
- Continuous variables remain continuous; `pp_runs` and `pp_run_rate` never appear together in the same complete-powerplay model.
- All generated datasets and artifacts remain ignored by Git unless a separate rights/release review clears them.

---

### Task 1: Snapshot and extraction audit

**Files:**
- Create: `src/odi_powerplay/audit.py`
- Create: `scripts/audit_extraction.py`
- Create: `tests/test_audit.py`
- Modify: `docs/transformation_log.md`

**Interfaces:**
- Consumes: `extract_match(path: str | Path) -> list[dict[str, Any]]` and `data/processed/powerplay_innings_primary.csv`.
- Produces: `select_audit_match_ids(rows, n, seed) -> list[str]`, `audit_raw_against_processed(raw_dir, processed_rows, match_ids) -> list[dict[str, Any]]`, and `artifacts/tables/extraction_audit.csv`.

- [ ] **Step 1: Write the deterministic-sampling test**

```python
def test_select_audit_match_ids_is_deterministic_and_unique():
    rows = [{"match_id": str(i), "year": 2015 + i % 3} for i in range(30)]
    first = select_audit_match_ids(rows, n=9, seed=20250905)
    second = select_audit_match_ids(rows, n=9, seed=20250905)
    assert first == second
    assert len(first) == len(set(first)) == 9
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python -m unittest tests.test_audit -v`
Expected: import failure for `odi_powerplay.audit`.

- [ ] **Step 3: Implement the audit module and CLI**

Use stable match-level sampling stratified by year, re-extract each selected raw JSON file, and compare the complete set of powerplay and metadata columns. Each audit row must contain `match_id`, `innings_number`, `field`, `processed_value`, `reextracted_value`, and `matches`.

- [ ] **Step 4: Generate and inspect the audit**

Run: `python scripts/audit_extraction.py --n-matches 20 --seed 20250905`
Expected: 40 innings audited, zero discrepancies, and a deterministic CSV saved under `artifacts/tables/`.

- [ ] **Step 5: Run the full tests and commit**

Run: `python -m unittest discover -s tests -v`
Expected: all tests pass.

```bash
git add src/odi_powerplay/audit.py scripts/audit_extraction.py tests/test_audit.py docs/transformation_log.md
git commit -m "Add deterministic Cricsheet extraction audit"
```

### Task 2: Leakage-safe pre-match team strength

**Files:**
- Create: `src/odi_powerplay/strength.py`
- Create: `scripts/build_team_strength.py`
- Create: `tests/test_strength.py`
- Modify: `docs/data_dictionary.md`

**Interfaces:**
- Consumes: one match row containing `match_id`, `match_date`, both teams, and winner.
- Produces: `calculate_prematch_strength(matches, initial_rating=1500.0, k_factor=20.0, rolling_window=20) -> list[dict[str, Any]]` and `data/processed/team_strength_pre_match.csv`.

- [ ] **Step 1: Write same-day leakage tests**

```python
def test_same_day_matches_receive_ratings_before_any_same_day_update():
    rows = [
        match("a", "2020-01-01", "A", "B", "A"),
        match("b", "2020-01-01", "A", "C", "C"),
    ]
    out = calculate_prematch_strength(rows)
    assert out[0]["team_1_elo_pre"] == 1500.0
    assert out[1]["team_1_elo_pre"] == 1500.0
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python -m unittest tests.test_strength -v`
Expected: import failure for `odi_powerplay.strength`.

- [ ] **Step 3: Implement Elo and rolling-20 strength**

Group matches by ISO date, emit both teams' ratings and prior decided-match win rates before applying the entire date's updates, and save `team_1_elo_pre`, `team_2_elo_pre`, `elo_difference_team_1`, prior-match counts, and rolling win rates.

- [ ] **Step 4: Build and audit the strength table**

Run: `python scripts/build_team_strength.py`
Expected: exactly one row per 1,093 primary match IDs, no duplicate IDs, and initial ratings for each team's first appearance.

- [ ] **Step 5: Run tests and commit**

```bash
python -m unittest discover -s tests -v
git add src/odi_powerplay/strength.py scripts/build_team_strength.py tests/test_strength.py docs/data_dictionary.md
git commit -m "Add leakage-safe pre-match team strength"
```

### Task 3: Outcome-blind pitch-source registry and validation

**Files:**
- Create: `src/odi_powerplay/pitch.py`
- Create: `scripts/validate_pitch_reports.py`
- Create: `scripts/select_pitch_batch.py`
- Create: `tests/test_pitch.py`
- Modify: `docs/pitch_collection_status.md`
- Modify: `docs/sources.md`

**Interfaces:**
- Consumes: `data/manual/pitch_reports.csv` and primary match IDs.
- Produces: `validate_pitch_rows(rows, match_index) -> tuple[list[dict], list[dict]]`, `select_next_pitch_batch(matches, audited_ids, quotas, seed) -> list[dict]`, and local `data/processed/pitch_reports_validated.csv` plus `artifacts/tables/pitch_validation_issues.csv`.

- [ ] **Step 1: Write source-timing and scale tests**

```python
def test_post_match_source_is_rejected():
    row = valid_pitch_row(published_at_utc="2024-01-02T12:00:00Z")
    match = {"match_start_utc": "2024-01-02T10:00:00Z"}
    valid, issues = validate_pitch_rows([row], {row["cricsheet_match_id"]: match})
    assert valid == []
    assert issues[0]["issue_code"] == "SOURCE_NOT_PRE_MATCH"

def test_pitch_scales_accept_only_documented_values():
    row = valid_pitch_row(batting_ease="4")
    valid, issues = validate_pitch_rows([row], {row["cricsheet_match_id"]: {}})
    assert any(item["issue_code"] == "INVALID_BATTING_EASE" for item in issues)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_pitch -v`
Expected: import failure for `odi_powerplay.pitch`.

- [ ] **Step 3: Implement validation and deterministic batch selection**

Enforce unique match IDs, venue/date agreement, documented ordinal scales, explicit blanks for unstated dimensions, eligible-source status, and publication-before-play when exact start time exists. Batch selection must use only ID/date/competition/venue metadata and must not read outcome or powerplay columns.

- [ ] **Step 4: Continue source collection in numbered batches**

For each selected match, search ESPNcricinfo/ICC first, then boards or established news, then established specialist outlets. Record a usable code, `source_no_pitch_evidence`, or `no_eligible_source`; never infer a pitch type from the match result or scorecard. Update only local working data and aggregate GitHub documentation.

- [ ] **Step 5: Validate, report coverage, and commit code/docs**

Run: `python scripts/validate_pitch_reports.py`
Expected: zero invalid usable rows; coverage counts reconcile to the local registry.

```bash
git add src/odi_powerplay/pitch.py scripts/validate_pitch_reports.py scripts/select_pitch_batch.py tests/test_pitch.py docs/pitch_collection_status.md docs/sources.md
git commit -m "Add auditable pitch-source registry validation"
```

### Task 4: Frozen analysis table and chronological splits

**Files:**
- Create: `src/odi_powerplay/analysis_table.py`
- Create: `scripts/build_analysis_table.py`
- Create: `tests/test_analysis_table.py`
- Create: `config/feature_allowlist.yaml`
- Modify: `docs/transformation_log.md`

**Interfaces:**
- Consumes: primary innings, match-level strength, and validated pitch tables.
- Produces: `build_analysis_table(innings, strength, pitch) -> list[dict]`, `assign_split(match_date) -> str`, `validate_no_leakage(rows, allowlist) -> list[str]`, local analysis CSVs, split manifests, and SHA-256 hashes.

- [ ] **Step 1: Write split and merge tests**

```python
def test_split_boundaries_are_chronological():
    assert assign_split("2023-12-31") == "development"
    assert assign_split("2024-01-01") == "validation"
    assert assign_split("2025-01-01") == "locked_test"

def test_both_innings_of_match_share_split():
    table = build_analysis_table(two_innings_fixture(), strength_fixture(), [])
    assert len({row["split"] for row in table}) == 1
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_analysis_table -v`
Expected: import failure for `odi_powerplay.analysis_table`.

- [ ] **Step 3: Implement one-to-one match merging and allowlist checks**

Merge strength and pitch at match level before expanding to innings. Save `team_elo_pre`, `opponent_elo_pre`, `elo_difference`, pitch missingness indicators, and the split label from date. Reject duplicate pitch/strength IDs and reject every predictor absent from `config/feature_allowlist.yaml`.

- [ ] **Step 4: Freeze manifests and hashes**

Run: `python scripts/build_analysis_table.py`
Expected: 2,186 full-cohort innings, a smaller explicitly reported pitch subset, no match crossing splits, and JSON manifests containing row counts and file hashes.

- [ ] **Step 5: Test and commit**

```bash
python -m unittest discover -s tests -v
git add src/odi_powerplay/analysis_table.py scripts/build_analysis_table.py tests/test_analysis_table.py config/feature_allowlist.yaml docs/transformation_log.md
git commit -m "Freeze leakage-safe chronological analysis tables"
```

### Task 5: Interpretable and nonlinear models

**Files:**
- Create: `src/odi_powerplay/modeling.py`
- Create: `scripts/train_models.py`
- Create: `tests/test_modeling.py`
- Create: `config/modeling.yaml`

**Interfaces:**
- Consumes: frozen full-cohort and pitch-subset analysis tables.
- Produces: `make_model_specs()`, `fit_model(spec, train_rows)`, `predict_model(model, rows)`, serialized fitted models, frozen parameters, and one prediction row per model/team-innings.

- [ ] **Step 1: Write model-matrix leakage tests**

```python
def test_runs_and_run_rate_never_share_a_specification():
    for spec in make_model_specs():
        assert not {"pp_runs", "pp_run_rate"}.issubset(spec.numeric_features)

def test_outcome_columns_never_enter_predictors():
    forbidden = {"winner", "batting_team_won", "final_total", "result_method"}
    for spec in make_model_specs():
        assert forbidden.isdisjoint(spec.all_features)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_modeling -v`
Expected: import failure for `odi_powerplay.modeling`.

- [ ] **Step 3: Implement nested model specifications**

Implement intercept-only, pre-match/context M0, runs+wickets benchmark, M1, and prespecified M2 interactions for penalized logistic regression. Add constrained Random Forest and shallow XGBoost challengers with preprocessing fit inside rolling-origin training folds.

- [ ] **Step 4: Tune only on development/validation data and freeze**

Run: `python scripts/train_models.py --fit-without-locked-test`
Expected: selected hyperparameters and serialized models saved without reading locked-test outcomes.

- [ ] **Step 5: Test and commit model code/config**

```bash
python -m unittest discover -s tests -v
git add src/odi_powerplay/modeling.py scripts/train_models.py tests/test_modeling.py config/modeling.yaml
git commit -m "Add nested chronological ODI models"
```

### Task 6: Evaluation, uncertainty, calibration, and interpretation

**Files:**
- Create: `src/odi_powerplay/evaluation.py`
- Create: `scripts/evaluate_models.py`
- Create: `scripts/make_figures.py`
- Create: `tests/test_evaluation.py`
- Modify: `docs/data_dictionary.md`

**Interfaces:**
- Consumes: frozen models and prediction rows.
- Produces: `compute_metrics(y, probability)`, `cluster_bootstrap_metrics(predictions, repetitions, seed)`, calibration tables, permutation importance, SHAP tables, marginal-probability grids, and required figures.

- [ ] **Step 1: Write metric and cluster-bootstrap tests**

```python
def test_perfect_probabilities_have_zero_brier_and_log_loss():
    result = compute_metrics([0, 1], [0.0, 1.0])
    assert result["brier_score"] == 0.0
    assert result["log_loss"] < 1e-12

def test_cluster_bootstrap_samples_whole_matches():
    samples = draw_cluster_indices(["m1", "m1", "m2", "m2"], seed=7)
    assert all(samples.count(i) == samples.count(i ^ 1) for i in range(4))
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_evaluation -v`
Expected: import failure for `odi_powerplay.evaluation`.

- [ ] **Step 3: Implement evaluation and 95% match-clustered intervals**

Calculate accuracy at 0.50, ROC-AUC, log loss, Brier score, calibration intercept/slope, and 2,000-repetition match-clustered percentile intervals using seed 20250905. Save every resample summary and the final metric table.

- [ ] **Step 4: Score the locked test once and generate graphics**

Run: `python scripts/evaluate_models.py --score-locked-test && python scripts/make_figures.py`
Expected: prediction CSVs, metric/CI tables, calibration curves, held-out permutation importance, SHAP summaries, and win-probability surfaces across runs, wickets, and supported pitch conditions.

- [ ] **Step 5: Test and commit**

```bash
python -m unittest discover -s tests -v
git add src/odi_powerplay/evaluation.py scripts/evaluate_models.py scripts/make_figures.py tests/test_evaluation.py docs/data_dictionary.md
git commit -m "Add calibrated evaluation and interpretation outputs"
```

### Task 7: Paper artifacts and reproducibility release

**Files:**
- Create: `scripts/reproduce.py`
- Create: `docs/results.md`
- Create: `docs/limitations.md`
- Modify: `README.md`
- Modify: `docs/paper_outline.md`
- Modify: `docs/ssac27_submission_plan.md`

**Interfaces:**
- Consumes: immutable inputs, frozen configuration, saved tables, and figures.
- Produces: a single-command local rebuild, output-hash comparison, final results narrative, limitations, and SSAC-ready abstract inputs.

- [ ] **Step 1: Implement ordered reproduction with explicit gates**

`scripts/reproduce.py` must run extraction audit, strength, pitch validation, analysis-table build, pre-test training, locked-test scoring, and figures in order; it exits nonzero on duplicate IDs, leakage violations, missing expected artifacts, failed tests, or hash mismatch.

- [ ] **Step 2: Reproduce from the fixed snapshot**

Run: `python scripts/reproduce.py`
Expected: the same cohort counts, split IDs, and hashes as the frozen manifests.

- [ ] **Step 3: Write results and limitations from saved artifacts**

Report associations rather than causation, distinguish full-cohort and pitch-subset results, disclose pitch-source coverage and measurement error, and state that ESPN commentary was not bulk extracted or used as a pre-match variable.

- [ ] **Step 4: Verify documentation and repository cleanliness**

Run: `git diff --check && python -m unittest discover -s tests -v && git status --short`
Expected: no whitespace errors, all tests pass, and only intended documentation/code changes appear.

- [ ] **Step 5: Commit and push**

```bash
git add scripts/reproduce.py docs/results.md docs/limitations.md README.md docs/paper_outline.md docs/ssac27_submission_plan.md
git commit -m "Document reproducible ODI powerplay results"
git push origin main
```

## Plan self-review

- Every requirement in `docs/research_design.md` maps to Tasks 1–7.
- Pitch collection is explicitly separated from outcome-bearing Cricsheet fields.
- Full-cohort modeling can proceed without pretending sparse pitch coverage is complete.
- Exact split boundaries, feature exclusions, metric definitions, bootstrap cluster, and random seed are fixed.
- No task requires automated extraction of ESPNcricinfo text.
- All downstream interfaces use `match_id`/`cricsheet_match_id` consistently at their declared merge boundary.
