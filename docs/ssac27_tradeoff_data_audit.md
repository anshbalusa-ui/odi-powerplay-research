# SSAC27 tradeoff data audit

**Status: BLOCKED for the fixed-snapshot claim; FIX_REQUIRED for any alternate-source run.** This clone does not contain the required Cricsheet archive SHA-256, and its 2025–2026 official archive candidate has a different hash. Thus exact fixed-snapshot results cannot be independently reproduced here. A separate 2015–2024-only run may be feasible after a pre-analysis source-version amendment and safe date/ID-filtered extraction; it must not be represented as reproduction of the fixed snapshot. No data-audit JSON is emitted before row-level checks.

## Snapshot availability (metadata-only)

Required archive SHA-256: `28350ee04a2ee710f959de939eb2240f737e684a2f7f93e00f3c2be26e4f415e`.

Checked `data/raw/cricsheet` and local named ODI ZIP candidates without opening/extracting match records. The fixed archive is not present. Three Downloads copies each hash to `24bd8b58a384a562f3dd59dbc284cd6b24cc8e4b484051f702f69ba72c5aac8d`, not the required snapshot. The controller's current official mutable-URL candidate, `data/raw/cricsheet/odis_json_20260929.zip`, hashes to `f8423531b24183bc2cfc1e3e27f9bd29ad7c4d5a4bdc2469bf681d7fe2f5c5ce`, also a mismatch. The controller reports comparing only the 942 outcome-blind registry IDs dated 2015–2024: all are present in both the Aug 3 and Sep 29 archives, and per-member SHA-256 values match with zero discrepancies. The newline-sorted `ID:SHA-256` mapping hashes to `5a1b3dcfec4c5d4e369ae79aa6d70722127ec7a5f7b9e92406001a1e4c98fb0a`. This materially supports an alternate-source unlocked run, but neither archive is the required Sept 10 snapshot, so the comparison cannot prove identity with that unavailable snapshot. I did not independently inspect archive member contents or metadata; no 2025+ member was opened for the controller-reported comparison. A broad home-directory filename search encountered macOS permission-denied paths; named-download and repository raw-directory checks completed.

Reproducible checks performed:

```text
find data/raw/cricsheet data/processed data/interim artifacts/tables -maxdepth 1 -type f -print
# data/raw/cricsheet contains .gitkeep and a nonmatching archive candidate;
# data/processed contains .gitkeep and two pitch-consensus CSVs;
# data/interim contains .gitkeep; no cohort/strength/venue/model table or manifest.

shasum -a 256 data/raw/cricsheet/odis_json_20260929.zip
# f8423531b24183bc2cfc1e3e27f9bd29ad7c4d5a4bdc2469bf681d7fe2f5c5ce

shasum -a 256 '/Users/anshbalusa/Downloads/odis_json.zip' \
  '/Users/anshbalusa/Downloads/odis_json (1).zip' \
  '/Users/anshbalusa/Downloads/odis_json (2).zip'
# all three: 24bd8b58a384a562f3dd59dbc284cd6b24cc8e4b484051f702f69ba72c5aac8d
```

The expected hash and historical September 10, 2026 retrieval date are documented in `README.md`; the project downloader's default URL is the mutable `https://cricsheet.org/downloads/odis_json.zip` (`scripts/download_cricsheet.py`). A download from that URL is not evidence of the fixed snapshot unless its archive hash matches exactly. The 942-match member hash comparison is an unlocked-ID comparison only; it does not establish byte-for-byte archive equality or the equivalence of non-cohort historical rows needed to recompute Elo/venue history.

## What the present artifacts establish—and do not

Tracked project prose reports a historical 1,094-match cohort (871 development, 71 2024 validation, 152 locked 2025+; 2,188 paired innings), but these are prior pipeline claims, **not independently reproduced in this clone**. `docs/pitch_expectation_method.md` explicitly records that raw Cricsheet and generated model table are absent and that cohort pairing is unverified (`cohort_pairing_verified=false`). `docs/modeling_status.md` records the previous full model-table hash `ea84ac198fde324c9e388d15ef57f253e055dc83de9307f53db5404d25e8e1b9`; the file itself is absent here, so that fingerprint cannot be checked against bytes. No match IDs, row counts, join rates, per-year counts, missingness, or feature/result values were recomputed. No 2025+ outcome record was opened or scored.

The only existing relevant leakage artifact, `artifacts/tables/pitch_expectation_leakage_audit.json` (SHA-256 `ead9606d8bfddc699b0f80589c69a291e792407cec247a45227ed2173c8b97ce`) and frozen run `artifacts/pitch_expectations/attempt_8_frozen/leakage_audit_20260929.json` (SHA-256 `ff3ce3a87d18a3bd54f249f3f7a3d53c4a158b238b26fe5b6c48e4fe4609651f`) concern the pitch-expectation input release, not the full ODI outcome table. They cannot establish full-cohort pairing, availability, splits, or non-pitch predictor leakage.

## Pipeline and leakage-path assessment

Code inspection—not an execution or data-level audit—finds these safeguards in the checked-in pipeline:

- `scripts/build_clean_dataset.py` requires `data/raw/cricsheet/source_manifest.json`, records the source archive hash in its generated summary, and emits all/clean/primary cohort tables and exclusion audits. Those required inputs and outputs are absent, so its historic counts cannot be verified here.
- `src/odi_powerplay/strength.py` requires exactly two innings per match; groups matches by date, emits each day's pre-update Elo and rolling win-rate history, then applies that date's results as a batch. Its intended pre-match features therefore exclude same-date and future results. This was not exercised against cohort rows.
- `src/odi_powerplay/venue.py` likewise requires two innings with matching date/venue; reads venue history before each date and appends that date's matches only afterward. Intended venue history is strictly earlier-date, not same-day. It was not exercised against cohort rows.
- `src/odi_powerplay/model_table.py` also has code-level guardrails: joins strength/venue by match ID with duplicate/missing/date/team checks; blocks result and source-provenance columns from predictors; and assigns splits from `match_date` (`<=2023-12-31` development, through `2024-12-31` validation, later locked) with an explicit cross-split-match rejection. `scripts/build_model_table.py` calls feature-allowlist validation. These static safeguards do not prove generated table values, split counts, full model call-site behavior, or that locked labels never enter fitting/scoring.
- Historical modeling documentation says both innings share a split and preprocessing fits on development only. Without the model table/IDs, match-level split pairing, cutoff membership, missingness handling, and absence of locked outcomes from model fitting/scoring are not independently established.
- The pipeline contains result-derived match outcome and Elo-history pathways by design. Their presence is not itself future leakage, but an exact-date, paired-match audit of inputs/outputs is needed to show only earlier-date outcomes feed pre-match context and that locked labels remain unconsumed. No runtime leakage claim is made here.

## Required recovery and proof

1. Obtain the archived September 10, 2026 Cricsheet ZIP (or another immutable copy of that exact retrieval), not merely the present-day downloader URL. Before extraction, compute SHA-256 on the archive bytes and require exact equality with `28350ee04a2ee710f959de939eb2240f737e684a2f7f93e00f3c2be26e4f415e`. Preserve the original archive; keep its URL/provenance, retrieval timestamp, and hash in `source_manifest.json`. If the candidate differs, stop and do not relabel it as the fixed snapshot.
2. If the fixed archive remains unavailable, first record a pre-analysis amendment naming the Sep 29 archive hash and limiting all outcome access to unlocked 2015–2024 members. The controller-reported exact SHA-256 match for the 942 registry members supports this alternative cohort input, but does not certify the missing Sept 10 archive; explicitly label any results as an amended-source 2015–2024 analysis. Retain pre-2015 history only as needed for dated pre-match Elo/venue state, and compare/hash those members separately before claiming continuity with prior feature construction. Do not open, extract, or score any 2025+ outcome member.
3. With exact fixed-source confirmation, or after approval of the alternate-source amendment, independently materialize cohort metadata/counts, exclusions and unlocked analysis rows; establish the locked boundary from metadata separately and retain locked records unopened.
4. Recompute match-level membership, exactly-two-innings pairing, both-innings-same-split, duplicate/orphan IDs, cohort/split counts, and missingness for every intended model variable. Hash generated tables/manifests; reconcile exact-source results against the historical 1,094/871/71/152 claims and saved model-table fingerprint where source bytes are available.
5. Audit joins and predictor lineage for outcome/target-derived fields, same-date and later match-result use, train-fitted preprocessing, temporal split leakage, and any path by which 2025+ outcomes can reach fit, tuning, feature selection, or scoring. Use the full-cohort audit documented in `README.md` only on verified unlocked data and preserve a separately documented lock check; do not claim the lock is proved solely because the split labels say `locked`.
Until either the exact snapshot and lock-safe audit are available, or an explicit pre-analysis source amendment is approved and its unlocked extraction/row-level checks pass, the analysis is not runnable as a reproducible fixed-snapshot tradeoff. Prior reported figures remain historical evidence, not this audit's result.