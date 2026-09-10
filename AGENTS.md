# Agent Working Agreement

This repository is a research project, not only a prediction demo. Changes must preserve reproducibility, source provenance, and the observational claim boundary.

## Shared branch

- Active integration branch: `research/full-odi-pipeline`.
- Do not push research changes directly to `main` while draft PR #1 is open.
- Before editing a file, read the current branch version because another agent may have changed it.
- Keep commits small and descriptive.

## Non-negotiable research rules

1. **Primary cohort:** all available clean men's ODIs in the fixed Cricsheet snapshot. World Cups are only a subgroup/sensitivity analysis unless the study design is explicitly changed.
2. **Powerplay window:** Cricsheet overs indexed 0 through 9. Preserve source-data edge cases such as umpire-miscounted overs; do not silently force every window to exactly 60 legal deliveries.
3. **Core powerplay features:** runs, wickets lost, boundary-ball percentage, dot-ball percentage, legal-ball count, and delivery-event count. Run rate is descriptive and is redundant with runs for ordinary complete ten-over windows.
4. **Outcome:** `batting_team_won`, one row per batting-team innings. Both innings from a match must remain in the same split/fold.
5. **Pitch evidence:** use only a source demonstrably published before match start. ESPNcricinfo is preferred when an eligible preview/conditions report exists, but missing ESPN coverage must remain missing rather than being guessed or replaced with post-match evidence.
6. **Outcome-blind pitch coding:** pitch-source discovery/coding queues must not expose winner, powerplay score, wickets, or other outcome information.
7. **Pitch provenance:** retain Cricsheet match ID, source URL, source title, publication time when available, verification status, coder/confidence, coded fields, and a short paraphrase. Do not copy large source passages.
8. **Weather:** historical environmental context comes from the free Open-Meteo archive API using ERA5. Keep raw response/audit metadata. Treat full-local-day summaries as contextual covariates, not exact innings weather unless verified start-time windows are later added.
9. **Team strength:** pre-match Elo may learn from prior decided men's ODIs even if those matches are excluded from the powerplay outcome cohort. Same-date updates must be batched to avoid within-day leakage.
10. **No future leakage:** no post-match articles, final totals, victory margin, player-of-match, end-of-period rankings, or features computed using future/test matches may enter predictors.
11. **Claim boundary:** this is a retrospective observational study. Use language such as `associated with`, `adjusted relationship`, or `estimated conditional win probability`; do not claim randomized causal effects.
12. **Missing data:** retain explicit missing/source-status flags. Never fabricate pitch/weather values to make joins complete.

## Engineering rules

- Follow test-driven development for behavior changes: failing test first, then minimal implementation, then full test suite.
- Current unit-test command: `python -m unittest discover -s tests -v`.
- Python sources and scripts must compile with `python -m compileall -q src scripts`.
- Generated raw/interim/processed datasets stay out of Git unless a specific redistribution decision is documented. Use GitHub Actions artifacts for reproducible generated outputs.
- Never overwrite raw source snapshots; keep source URL, retrieval timestamp, and checksum/manifest.
- Raise on duplicate match-level context rows rather than silently multiplying team-innings rows.

## Current build order

1. Validate the full Cricsheet cohort and extraction invariants.
2. Finish auditable venue geocoding and historical weather coverage.
3. Produce the complete outcome-blind pitch-source collection queue.
4. Collect and code eligible pre-match pitch reports in deterministic batches; record unavailable sources explicitly.
5. Build the context-enriched team-innings analysis table with leakage-safe Elo.
6. Freeze chronological development/validation/test periods before modeling outcomes.
7. Fit interpretable baseline/nested models before nonlinear challengers.
8. Report discrimination, proper scoring rules, calibration, uncertainty, and marginal relationships—not accuracy alone.

## Coordination

If an agent discovers a design conflict or source-quality problem, document it in the PR or research docs before changing the study definition. Prefer transparent missingness and a smaller defensible sample over a larger dataset built from unverifiable assumptions.
