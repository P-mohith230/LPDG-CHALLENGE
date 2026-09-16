# Project Context Changelog
**LPDG Innovation Hub Selection Challenge 2026**  
*Chronological Audit Trail of Evidentiary and Methodological Evolutions*

---

## Change Record: 2026-09-15 (Ingestion of FAQ Round 2 & Submission Email)

### Entry 2026-09-15.01: Institutional Submission Deadline Discrepancy
- **DATE**: 2026-09-15
- **SOURCE**: NEXORA 2026 Project Submission Email (from `hcseds@rgmcet.edu.in`)
- **OLD UNDERSTANDING**: Project hand-in deadline was 23:59 IST on Wednesday 16 September 2026 (per LPDG Brief and FAQ Round 1 §1.1).
- **NEW UNDERSTANDING**: The institutional submission deadline via Google Form (`https://forms.gle/qHZqsRRPGWf8ja5S6`) is **20:00 IST on Wednesday 16 September 2026** (almost 4 hours earlier). Furthermore, only the first submission will be considered; duplicate submissions are summarily rejected.
- **WHY IT CHANGED**: The local institutional evaluation committee issued binding submission guidelines for RGMCET candidates.
- **FILES UPDATED**: `FINAL_SUBMISSION_REQUIREMENTS.md`, `LPDG_RULE_COMPLIANCE_CHECKLIST.md`, `LPDG_2026_Project_Context.md`, `LPDG_2026_Round2_Context.md`.
- **PROJECT IMPACT**: Internal code and video freeze shifted up to 18:00 IST on 16 September.

---

### Entry 2026-09-15.02: Fault Episode Accounting & Re-visit Penalty Mechanics
- **DATE**: 2026-09-15
- **SOURCE**: FAQ — Round Two, and final §4.1
- **OLD UNDERSTANDING**: It was ambiguous whether re-visiting a gateway in consecutive weeks would incur wasted dispatch penalties or whether the scoring script simulated counterfactual repair of telemetry.
- **NEW UNDERSTANDING**: Fault episodes are maximal runs of consecutive faulty weeks pre-calculated in hidden ground truth, separated by $\ge 1$ healthy week. Telemetry does NOT heal counterfactually. Only the earliest visit within an episode stops €600 accrual. Re-visiting the same gateway within the same episode confers zero savings, wastes €380, and consumes one of the 15 weekly slots.
- **WHY IT CHANGED**: LPDG directly answered our Question 1 in §4.1.
- **FILES UPDATED**: `LPDG_2026_Round2_Context.md`, `PROJECT_DECISION_REGISTER.md`, `EXPERIMENT_BACKLOG.md`.
- **PROJECT IMPACT**: Dispatch policy must be state-aware, implementing a cooldown suppression filter on recently visited gateways.

---

### Entry 2026-09-15.03: Telemetry Absence vs. Zero-Filled Records
- **DATE**: 2026-09-15
- **SOURCE**: FAQ — Round Two, and final §3.4
- **OLD UNDERSTANDING**: Assumed missing hourly telemetry might be filled with zeros or represented as empty rows.
- **NEW UNDERSTANDING**: Telemetry is physically sparse. Missing hours are omitted rows, not zero-filled rows. Loader logic must reindex against a complete time grid to detect silence.
- **WHY IT CHANGED**: LPDG warned: *"Do not assume the physical layout matches the logical grid... check what your loader actually produces before building a silence detector."*
- **FILES UPDATED**: `LPDG_2026_Round2_Context.md`, `ROUND2_UNANSWERABLE_QUESTIONS_ANALYSIS.md`, `EXPERIMENT_BACKLOG.md`.
- **PROJECT IMPACT**: Ingestion pipeline must generate a full hourly calendar grid to explicitly identify absent timestamps.

---

### Entry 2026-09-15.04: Evaluation Primacy of Operational Cost Over Statistical Metrics
- **DATE**: 2026-09-15
- **SOURCE**: FAQ — Round Two, and final §4.2
- **OLD UNDERSTANDING**: F1-score or Precision@15 might serve as auxiliary proxy evaluation criteria.
- **NEW UNDERSTANDING**: Models are judged strictly on total operational cost. A model with superior F1 but worse cost is officially marked as losing. Accuracy and F1 are uncalibrated for asymmetric costs (€380 vs. €600 recurring) and hard capacity caps.
- **WHY IT CHANGED**: LPDG explicitly stated that F1 treats false positives and false negatives as comparable, which they are not in this operational setting.
- **FILES UPDATED**: `LPDG_2026_Round2_Context.md`, `ROUND2_PROJECT_CLUES.md`.
- **PROJECT IMPACT**: Custom `CostEvaluator` formalized as the sole loss/selection metric.

---

### Entry 2026-09-15.05: Deterministic Secondary Tie-Breaking Mandate
- **DATE**: 2026-09-15
- **SOURCE**: FAQ — Round Two, and final §3.6
- **OLD UNDERSTANDING**: Arbitrary tie-breaking was common in baseline implementations.
- **NEW UNDERSTANDING**: Random tie-breaking is an explicit defect. Secondary sorting keys (e.g. `n_meters_installed`, `gateway_id`) are mandatory to guarantee deterministic outputs across platforms.
- **WHY IT CHANGED**: FAQ §3.6 designated random tie-breaking without a seed as "actually wrong" and declared non-deterministic outputs as a bug during live sessions.
### Entry 2026-09-15.06: Master Documentation Architecture & Subdirectory Reorganization
- **DATE**: 2026-09-15
- **SOURCE**: Project Governance Protocol
- **OLD UNDERSTANDING**: Documentation files sat in a flat list in `docs/` with early scratch files mixed with master context files.
- **NEW UNDERSTANDING**: A clean 7-folder modular documentation architecture established (`01_context`, `02_decisions`, `03_data`, `04_ml`, `05_experiments`, `06_submission`, `07_compliance`, and `99_archive/legacy_phase_audits`). Legacy scratch audits synthesized and moved to archive; zero unverified or invented results committed.
- **WHY IT CHANGED**: User directive to formalize a rigorous, professional, revision-friendly documentation system before proceeding to empirical modeling.
- **FILES CREATED / UPDATED**:
  - `docs/02_decisions/RESEARCH_QUESTIONS.md` (Created)
  - `docs/03_data/DATA_AUDIT_REPORT.md` (Created)
  - `docs/03_data/DATA_AVAILABILITY_AND_CUTOFF.md` (Created)
  - `docs/03_data/FEATURE_REGISTRY.md` (Created)
  - `docs/04_ml/TARGET_DEFINITION.md` (Created)
  - `docs/04_ml/BASELINE_EVALUATION.md` (Created)
  - `docs/04_ml/VALIDATION_PLAN.md` (Created)
  - `docs/04_ml/COST_EVALUATION.md` (Created)
  - `docs/04_ml/MODEL_CARD.md` (Created)
  - `docs/05_experiments/EXPERIMENT_RESULTS.md` (Created)
  - `docs/06_submission/FINAL_RESULTS.md` (Created)
  - `docs/06_submission/PREDICTION_AUDIT.md` (Created)
  - `docs/07_compliance/REPRODUCIBILITY.md` (Created)
  - Archived 10 legacy files into `docs/99_archive/legacy_phase_audits/`.
- **PROJECT IMPACT**: Clean separation of facts vs. inferences vs. candidate decisions; clear tracking of open items.

---

## Change Record: 2026-08-31 (Ingestion of FAQ Round 1 & Baseline Audit)

### Entry 2026-08-31.01: Replaced Challenge Schedule
- **DATE**: 2026-08-31
- **SOURCE**: 03-FAQ-Round-1.pdf §1.1
- **OLD UNDERSTANDING**: 3-week project schedule per Brief p. 6.
- **NEW UNDERSTANDING**: 18-day compressed schedule starting 29 August and ending 16 September 2026.
- **FILES UPDATED**: `LPDG_2026_Project_Context.md`.

### Entry 2026-08-31.02: CSV Encoding & Gateway ID Mismatches
- **DATE**: 2026-08-31
- **SOURCE**: Forensic Data Audit
- **OLD UNDERSTANDING**: Standard UTF-8 reading and uniform MAC address IDs.
- **NEW UNDERSTANDING**: CSV files are `latin1` encoded; `meter_read_success.csv` and telemetry use 12-char bare hex, while master/visits use 17-char colon hex.
- **FILES UPDATED**: `data_audit.md`, `LPDG_2026_Project_Context.md`.
