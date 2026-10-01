# SSAC27 Data Availability and Reproduction

This document identifies the exact public input used for the current SSAC27 analysis and the repository path used to reproduce the analyzed cohort.

## Public match-data source

The current analysis uses the public Cricsheet men's ODI JSON archive:

- Source page: https://cricsheet.org/downloads/
- Download used by the reproducibility script: https://cricsheet.org/downloads/odis_json.zip
- Frozen September 29, 2026 archive SHA-256: `f8423531b24183bc2cfc1e3e27f9bd29ad7c4d5a4bdc2469bf681d7fe2f5c5ce`

Cricsheet publicly provides ODI match data in JSON format. The repository does **not** relicense or republish the raw third-party archive. Instead, it provides the public source link, frozen archive identity, tracked cohort registry, deterministic materialization code, and audits needed to recover the exact analyzed input.

## Exact cohort selection

The locked-safe materializer is:

`scripts/materialize_ssac27_unlocked_raw.py`

Its tracked registry input is:

`data/manual/match_start_times_template.csv`

The materializer:

1. verifies the downloaded archive against the frozen SHA-256;
2. selects only prespecified 2015–2024 registry match IDs;
3. requires exactly 942 unlocked matches;
4. verifies each selected member's date, gender, and ODI identity;
5. records per-member SHA-256 hashes and a source manifest;
6. treats 2025+ registry entries as metadata only and does not open their JSON bodies.

The current analyzed cohort is 942 clean men's ODI matches / 1,884 paired innings, split into 871 development matches through 2023 and 71 untouched 2024 temporal-validation matches.

## Reproduction

From the repository root:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .

curl -fL https://cricsheet.org/downloads/odis_json.zip \
  -o data/raw/cricsheet/odis_json_20260929.zip

.venv/bin/python scripts/materialize_ssac27_unlocked_raw.py
.venv/bin/python scripts/build_clean_dataset.py \
  --input-dir data/raw/cricsheet/unlocked_20260929
.venv/bin/python scripts/build_team_strength.py
.venv/bin/python scripts/build_venue_conditions.py
.venv/bin/python scripts/build_model_table.py
.venv/bin/python scripts/audit_full_cohort_analysis.py \
  --summary-output artifacts/ssac27_tradeoff/data_audit.json
.venv/bin/python scripts/run_ssac27_tradeoff_pipeline.py
.venv/bin/python scripts/audit_ssac27_tradeoff_results.py
.venv/bin/python scripts/release_ssac27_tradeoff_results.py
.venv/bin/python -m unittest discover -s tests -v
```

If the mutable Cricsheet download no longer matches the frozen September 29 SHA-256, the materializer fails closed rather than silently analyzing a different source snapshot.

## Submission note

The SSAC27 competition requires an open-source repository supporting the research and its data inputs. This repository supplies the public input source, exact source hash, tracked selection metadata, code, tests, audits, and aggregate evidence required to reproduce the current analysis while avoiding unauthorized relicensing of third-party raw data.

The current research claim set is controlled by:

- `docs/ssac27_submission_source_of_truth.md`
- `docs/ssac27_numeric_handoff.md`
- `docs/ssac27_abstract_skeleton.md`
