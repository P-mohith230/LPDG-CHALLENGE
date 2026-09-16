# LPDG 2026 Final Submission Checklist

**Project**: LPDG Innovation Hub Selection Challenge 2026  
**Candidate Registration ID**: `23091a3286`  
**Submission Date**: 16 September 2026  

---

## Required Deliverables

- [x] **`predictions.csv`**: Verified production file (120 rows, 8 weeks, 15/week).
- [x] **Code that produced `predictions.csv`**: Complete source in `src/`, entrypoints `run.py` and `run.sh`.
- [x] **`DECISIONS.md`**: Five required project decisions, alternatives, trade-offs, limitations, and Part 2 track selection.
- [x] **`AI-USAGE.md`**: AI usage disclosure, caught mistakes, and verification protocols.
- [x] **`README.md`**: Comprehensive project guide, architecture diagrams, execution steps, and limitations.
- [x] **Part 2 Work**: Track E (Machine Learning) complete with ablation, dual validation, and baseline outperformance.
- [ ] **6–8 Minute Screen Recording**: Script prepared in `docs/SCREEN_RECORDING_SCRIPT.md`; *Pending final video recording and upload by candidate*.

---

## Technical Verification

- [x] **120 prediction rows**: Verified exactly 120 rows.
- [x] **15 per week**: Exactly 15 dispatches per week across 8 scored weeks.
- [x] **8 weeks**: `2026-02-02` to `2026-03-23` inclusive.
- [x] **Official validator exit 0**: `predictions.csv: OK` confirmed by official grader script.
- [x] **Deterministic predictions**: 100% byte-for-byte SHA256 match across dual independent executions (`f2712079...`).
- [x] **Baseline immutable**: `baseline_v1_predictions.csv` matches recorded manifest SHA256 (`14be8c30...`).
- [x] **Full tests passing**: 70 / 70 automated tests passing (100% GREEN, 0 failures, 0 errors).
- [x] **Temporal leakage protection**: Observation cutoff strictly before Monday 00:00:00 UTC; programmatic firewall verified.
- [x] **Gateway-disjoint validation**: 5-Fold GroupKFold with 0% gateway overlap verified.
- [x] **Economic evaluation**: Unified 16-week window, 240 visits, €380/visit, €600/fault penalty rigorously verified.
- [x] **No hidden ground truth**: Uses proxy operational target ($Y = \text{read\_ratio} < 0.50$); does not assume unreleased labels.
- [x] **No future information**: Zero lookahead in feature engineering or model training.
- [x] **No runtime internet dependency**: Runs 100% offline.
- [x] **No runtime API key**: Requires zero credentials or external services.
- [x] **No challenge data committed**: Raw data directories (`data/`, `*.parquet`) guarded by `.gitignore`.

---

## Documentation

- [x] **`README.md` complete**: Clear executive summary, C3 architecture diagram, one-command execution instructions.
- [x] **`DECISIONS.md` complete**: All five decisions documented with alternatives, rationale, and trade-offs.
- [x] **`AI-USAGE.md` complete**: Concrete errors documented (register duplication, German site mapping, hour counting).
- [x] **Part 2 area clearly stated**: Track E (Machine Learning) explicitly documented across all files.
- [x] **Five decisions documented**: Target, Features, Model, Cooldown, Part 2 Track.
- [x] **Alternatives documented**: At least 2 alternatives documented for each decision.
- [x] **C3 architecture documented**: Promoted Champion Pipeline clearly detailed.
- [x] **Innovation results documented**: Innovations 1 through 5 fully documented with quantitative matrices.
- [x] **Rejected novelty documented**: Rejection of Innovation 5 from primary dispatch fully justified with forensic data.
- [x] **Limitations documented**: Sub-weekly resolution, static cooldown, and proxy-target disconnect costed.
- [x] **Screen recording script prepared**: `docs/SCREEN_RECORDING_SCRIPT.md` ready with 7-minute cue sheet.
- [ ] **Recording link added once available**: Placeholder in `README.md` to be updated upon video upload.
