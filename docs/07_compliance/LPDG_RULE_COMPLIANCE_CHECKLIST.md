# Master LPDG Rule Compliance Checklist
**LPDG Innovation Hub Selection Challenge 2026**  
*Verification Matrix Across Data, Modeling, Repository, Runtime, and Submission Protocols*

---

## Overview
This checklist serves as the authoritative compliance verification gate for all project artifacts. Before any code is committed, model artifact finalized, or submission file approved, it must be verified against this master register.

Statuses used:
- **`PASS`**: Verified and confirmed compliant.
- **`NOT YET TESTED`**: Rule understood; pending final artifact generation or test run.
- **`OPEN`**: Candidate decision pending empirical resolution.
- **`FAIL`**: Non-compliant (blocks submission).
- **`NOT APPLICABLE`**: Excluded based on chosen Part 2 track.

---

## Section A: Data Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **A-01** | Do not commit the raw challenge dataset (104 MB) to git. | Brief p. 5, FAQ Round 1 §1.2, FAQ Round 2 §2.2 | **PASS** | `.gitignore` contains `data/`, `*.parquet`, `*.zip`, `03-challenge-data/`. Verified with `git status`. |
| **A-02** | Handle CSV file encoding (`latin1`/`cp1252`) explicitly. | Data Audit, FAQ Round 1 §4.7 | **PASS** | All pandas ingestion calls explicitly pass `encoding='latin1'`. |
| **A-03** | Normalize all gateway IDs (strip colons, uppercase hex). | Data Audit, FAQ Round 1 §2.5 | **PASS** | Ingestion pipeline applies `.str.replace(':', '').str.upper()` across all joins. |
| **A-04** | Do not hardcode the 8 provided monthly telemetry partitions. | FAQ Round 2 §7.1 | **PASS** | Partition loader uses dynamic discovery `sorted(glob('data/telemetry/month=*'))`. |
| **A-05** | Filter out gateways decommissioned prior to decision Monday. | Data Audit, FAQ Round 1 §4.1 | **NOT YET TESTED** | Filter asserts `decommissioned_on > monday` or null before dispatching. |
| **A-06** | Do not dispatch to future-installed gateways (installed post-March 2026). | Data Audit | **NOT YET TESTED** | Filter asserts `installed_on <= monday`. |
| **A-07** | Do not apply blanket `fillna(0)` across all telemetry columns. | FAQ Round 2 §3.2 | **OPEN** | Document column-by-column imputation mapping in `DECISIONS.md`. |

---

## Section B: Temporal Cutoff Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **B-01** | For Monday $T$, use strictly data timestamped prior to Monday 00:00:00 UTC. | Brief p. 2, FAQ Round 1 §3.6, §3.7 | **NOT YET TESTED** | Assertion in feature pipeline: `assert (df['ts_utc'] < monday_iso).all()`. |
| **B-02** | Use consistent timezone convention (Monday 00:00:00 UTC) across all files. | FAQ Round 1 §3.7 | **PASS** | UTC timestamps enforced everywhere; no mixing with local Berlin midnight. |
| **B-03** | Do not use `engineer_review_2026-02.xlsx` for Week 1 (2026-02-02) or Week 2 (2026-02-09). | FAQ Round 1 §3.8, FAQ Round 2 §3.1 | **NOT YET TESTED** | Ingestion gate asserts `week_start >= '2026-02-16'` before loading review data. |
| **B-04** | Contemporary weekly row in `meter_read_success.csv` is unavailable at prediction time. | FAQ Round 1 §3.8 | **PASS** | File naturally ends on `2026-01-26`; lagged features only look at prior weeks. |
| **B-05** | Do not use future historical telemetry to predict current week features. | FAQ Round 1 §6.13, FAQ Round 2 §4.5 | **NOT YET TESTED** | Feature calculation window strictly bounded by $t < T$. |

---

## Section C: Machine Learning Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **C-01** | Model must beat `baseline_3sigma.py` on total cost, not accuracy or F1. | Brief p. 4, FAQ Round 2 §4.2 | **NOT YET TESTED** | Evaluate via `CostEvaluator`; assert $	ext{Cost}_{	ext{ML}} < 	ext{Cost}_{	ext{Baseline}}$. |
| **C-02** | Validation must be device-disjoint (gateways never seen in training). | Brief p. 4, FAQ Round 1 §6.12, FAQ Round 2 §5.2 | **NOT YET TESTED** | GroupKFold on `gateway_id`; assert zero gateway ID overlap between train and test. |
| **C-03** | Validation must be forward-in-time (evaluating weeks after training). | Brief p. 4, FAQ Round 1 §6.12, FAQ Round 2 §5.2 | **NOT YET TESTED** | Temporal train/test split on January 2026 holdout. |
| **C-04** | Report validation metric spread / fold variation, not just point estimates. | FAQ Round 2 §5.2 | **NOT YET TESTED** | Summary tables output Mean, Std, Min, Max across all 5 folds. |
| **C-05** | Do not treat unvisited gateways as true negative examples without justification. | FAQ Round 1 §4.4, FAQ Round 2 §4.4 | **OPEN** | PU learning or objective physical failure standard documented in `DECISIONS.md`. |
| **C-06** | Decouple training code from inference execution. | Brief p. 4, FAQ Round 1 §6.14, FAQ Round 2 §7.2 | **NOT YET TESTED** | `src/train.py` creates model artifact; `src/predict.py` executes in $<30	ext{s}$. |

---

## Section D: Ranking & Output Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **D-01** | `predictions.csv` must contain exactly 120 rows (15 rows × 8 weeks). | Brief p. 2, FAQ Round 1 §3.4, `validate_submission.py` | **NOT YET TESTED** | Automated check with `python validate_submission.py predictions.csv`. |
| **D-02** | Ranks within each week must be strictly 1 to 15 with no repeats. | `validate_submission.py` | **NOT YET TESTED** | Verified by validator script. |
| **D-03** | No duplicate gateway ID within the same week. | `validate_submission.py` | **NOT YET TESTED** | Verified by validator script. |
| **D-04** | Tie-breaking must be strictly deterministic across platforms. | FAQ Round 2 §3.6 | **NOT YET TESTED** | Multi-key sort: `['score', 'n_meters_installed', 'gateway_id']`. |
| **D-05** | Numeric score column must be non-null on all rows. | `validate_submission.py` | **NOT YET TESTED** | Verified by validator script. |
| **D-06** | Reason string must be non-empty and $\le 300$ characters. | Brief p. 2, `validate_submission.py` | **NOT YET TESTED** | String length assertion `(df['reason'].str.len() <= 300).all()`. |
| **D-07** | Reason string must be written for the operations manager, not a raw feature dump. | FAQ Round 1 §3.5, FAQ Round 2 §5.3 | **NOT YET TESTED** | Human review of template output. |

---

## Section E: Cost & Evaluation Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **E-01** | Dispatched visit cost is flat €380 once per visit (€45,600 baseline across 120 slots). | FAQ Round 1 §5.2 | **PASS** | Codified in `CostEvaluator`. |
| **E-02** | Unaddressed fault penalty is flat €600 per gateway per week (not scaled by meters). | FAQ Round 1 §5.3 | **PASS** | Codified in `CostEvaluator`. |
| **E-03** | Only the earliest visit within a hidden fault episode halts €600 accrual. | FAQ Round 2 §4.1 | **NOT YET TESTED** | Unit test on episode tracking logic in `CostEvaluator`. |
| **E-04** | Repeat visits within the same episode cost €380, burn a slot, and save €0. | FAQ Round 2 §4.1 | **NOT YET TESTED** | Unit test asserting zero cost reduction on intra-episode repeat dispatches. |
| **E-05** | Sub-threshold decisions (warranting $<15$ visits) must be defended in `DECISIONS.md`. | FAQ Round 1 §3.4 | **OPEN** | Document exact theoretical savings in `DECISIONS.md`. |

---

## Section F: Repository & Packaging Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **F-01** | Repository must be completely PRIVATE until final hand-in deadline. | Brief p. 5, FAQ Round 1 §1.2 | **PASS** | Confirmed private on GitHub. |
| **F-02** | Repository must be flipped to PUBLIC before the hand-in deadline. | Brief p. 5, NEXORA Submission Email | **NOT YET TESTED** | Scheduled for 16 September 2026, 18:00 IST. |
| **F-03** | Git commit history must demonstrate normal, iterative progress (no single giant commit). | Brief p. 2 | **NOT YET TESTED** | Frequent granular commits with meaningful messages. |
| **F-04** | Commit history must contain zero API keys, tokens, or passwords. | Brief p. 5, FAQ Round 1 §1.2 | **PASS** | Git history scanner run prior to making public. |
| **F-05** | Candidate resume placed at repository root named `<Registration_Id.pdf>`. | NEXORA Submission Email | **NOT YET TESTED** | Copy resume to `m:\LPDGE91a3286.pdf`. |

---

## Section G: Offline & Runtime Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **G-01** | One command starts the entire solution (`docker compose up`, `make run`, or `./run.sh`). | Brief p. 2, FAQ Round 1 §2.1, FAQ Round 2 §2.3 | **NOT YET TESTED** | Test execution on foreign machine / clean VM. |
| **G-02** | Default data path must be `./data/` and accept `--data <path>` override. | Brief p. 5, FAQ Round 1 §2.1 | **NOT YET TESTED** | Test with `--data /custom/path`. |
| **G-03** | Solution must run 100% offline with zero internet access, API keys, or cloud downloads. | Brief p. 2, FAQ Round 1 §2.1, FAQ Round 2 §2.5 | **NOT YET TESTED** | Execute with physical/virtual network disabled. |
| **G-04** | Solution must execute within normal laptop resources (8–16 GB RAM, CPU-only). | FAQ Round 1 §2.4 | **NOT YET TESTED** | Profiling with `memory_profiler` ensuring peak RAM $<2	ext{ GB}$. |
| **G-05** | Pipeline runtime must be reasonable ($<5	ext{ minutes}$). | FAQ Round 1 §2.4 | **NOT YET TESTED** | Timed execution benchmark. |

---

## Section H: Documentation Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **H-01** | `README.md` must provide setup steps clear enough for a stranger to run without asking. | FAQ Round 1 §1.4 | **NOT YET TESTED** | Peer review / fresh environment run from README steps. |
| **H-02** | `DECISIONS.md` must document 5 major choices, including alternatives considered & rejected. | Brief p. 2, FAQ Round 2 §5.3 | **NOT YET TESTED** | Verify all 5 decisions list explicit rejected alternatives. |
| **H-03** | Exactly one decision in `DECISIONS.md` must state the chosen Part 2 area and justify why. | Brief p. 2 | **NOT YET TESTED** | Explicit section in `DECISIONS.md`. |
| **H-04** | `AI-USAGE.md` must declare AI tool use and document at least one error caught and corrected. | Brief p. 2, FAQ Round 1 §2.5 | **NOT YET TESTED** | Document merge failure / encoding catch. |
| **H-05** | Limitations section ("What it cannot do") must list 3 real, costed weaknesses. | Brief p. 2, FAQ Round 2 §5.3, §5.4 | **NOT YET TESTED** | Documented in `DECISIONS.md` and report. |
| **H-06** | Screen recording (6–8 mins) must be linked in `README.md` and open in incognito window. | Brief p. 2, FAQ Round 2 §2.1 | **NOT YET TESTED** | Test link in private browser window. |

---

## Section I: Model Artifact Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **I-01** | Model artifacts (`.pkl`, `.joblib`) must be included in the GitHub repository only. | NEXORA Submission Email | **NOT YET TESTED** | Check `git ls-files` for serialized model file. |
| **I-02** | Model artifact file size must be small ($<1	ext{–}2	ext{ MB}$); cannot contain raw data slices. | FAQ Round 2 §2.2 | **NOT YET TESTED** | Verify `ls -lh model.joblib` is $<2	ext{ MB}$. |
| **I-03** | Model artifact must include version identifier and input parameter hash. | Brief p. 4 (Track F), FAQ Round 2 §2.2 | **NOT YET TESTED** | Companion `model_metadata.json` with hash and version string. |

---

## Section J: Live-Session Rules

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **J-01** | Pipeline must ingest unseen monthly partition (e.g. `month=2026-04`) without crashing. | FAQ Round 2 §7.1 | **NOT YET TESTED** | Mock unseen partition test with dummy April 2026 data. |
| **J-02** | Pipeline must handle unseen or newly quiet gateways without throwing key errors. | FAQ Round 2 §7.1 | **NOT YET TESTED** | Mock unseen gateway ID test. |
| **J-03** | Candidate must rehearse the live modification (move threshold / adapt model) beforehand. | FAQ Round 2 §7.2 | **NOT YET TESTED** | Dry-run threshold adjustment script. |
| **J-04** | Candidate must narrate diagnostic steps when code encounters errors during live demo. | FAQ Round 2 §5.3 | **NOT YET TESTED** | Presentation rehearsal. |

---

## Section K: Submission Email Rules (NEXORA 2026 / RGMCET)

| Rule ID | Rule Statement | Source | Status | How We Will Verify It |
|---|---|---|---|---|
| **K-01** | Submit project details via official Google Form (`https://forms.gle/qHZqsRRPGWf8ja5S6`). | NEXORA Submission Email | **NOT YET TESTED** | Submit form before 20:00 IST on 16 Sep 2026. |
| **K-02** | Strictly observe the 20:00 IST deadline on 16 September 2026 (Night 8:00 IST). | NEXORA Submission Email | **NOT YET TESTED** | Target internal submission freeze at 18:00 IST. |
| **K-03** | Use official institutional email (`23091a3286@rgmcet.edu.in`); personal emails prohibited. | NEXORA Submission Email | **PASS** | Verified official student email address. |
| **K-04** | Ensure only ONE submission is made via Google Form (duplicates rejected summarily). | NEXORA Submission Email | **NOT YET TESTED** | Strict single submission verification. |
| **K-05** | Attend in-person evaluation at RGMCET campus on 18 September 2026, 9:00 AM. | NEXORA Submission Email | **NOT YET TESTED** | Calendar reminder set. |
