# Challenge Understanding & Plain-Language Reconstruction
**LPDG Innovation Hub Selection Challenge 2026**  
*Forensic Documentation Analysis & Plain-Language Breakdown*

---

## Section 1: Official Documentation Extraction (Phase 1)

### A. Exact Challenge Objective
The challenge requires candidates to build an automated decision system that analyzes historical and streaming telemetry/operations data from a smart utility radio network of ~320 gateways. For each of **8 consecutive Mondays** (from 2 February 2026 to 23 March 2026), the system must select and rank exactly **15 gateways** to be visited by field technicians during that week, providing a human-readable, domain-relevant justification (≤ 300 characters) for each recommendation.

### B. Part 1 Requirements (Universal Core Gate)
Part 1 is mandatory for all candidates regardless of track. It operates as a strict **Pass/Fail filter**:
1. **Automated One-Command Execution**: Must run with a single command on a clean machine (e.g., `docker compose up`, `make run`), reading data from a directory named `data` (defaulting to `./data` and accepting `--data <path>`).
2. **Standard Output**: Must output a valid CSV file named `predictions.csv` containing exactly 120 rows (15 gateways × 8 weeks) with columns: `week_start`, `rank`, `gateway_id`, `score`, `reason`.
3. **Format Validation**: Must pass `validate_submission.py` with exit code 0.
4. **Required Documentation**:
   - `DECISIONS.md`: Explaining five key technical/architectural choices, including alternatives considered and rejection rationales. Exactly one choice must explicitly state the chosen Part 2 specialization area and justify the selection.
   - `AI-USAGE.md`: Full disclosure of AI tool usage, including at least one specific instance where an AI tool made an error that the candidate identified and corrected.
   - Identification of system limitations ("What it cannot do"): Explicit failure modes and what an additional two weeks of engineering would address.
5. **Engineering Hygiene**: Clean, chronological Git commit history demonstrating iterative development (single "giant commit" at the end is disallowed).
6. **Video Walkthrough**: A 6 to 8-minute screen recording demonstrating what was built, how it runs, and walking through at least one concrete result.

### C. Part 2 Requirements (Vertical Specialization Tracks)
Candidates must select **one** of six specialized engineering disciplines:

| Discipline | Core Directive | Key Evaluation Requirements |
|---|---|---|
| **A — Data Engineering** | Build a resilient, production-grade data pipeline | • Multi-stage raw-to-clean data processing pipeline.<br>• Idempotent execution (safe to re-run without duplication).<br>• Incremental processing (only processes new data partitions).<br>• Fail-fast data contract checks and schema assertions.<br>• Written data quality documentation and data audit note. |
| **B — Software Development** | Build maintainable, modular software service | • Clean Web API (endpoints for weekly top 15, single gateway drill-down, rerun trigger).<br>• Comprehensive test suite (unit tests, integration test, plus a regression test from a discovered bug).<br>• Decoupled architecture (pluggable ranking logic separate from API interface).<br>• Robust error handling for edge cases (missing data, malformed IDs).<br>• Self-contained API documentation. |
| **C — DevOps** | Containerized, observable, self-healing deployment | • Fully containerized execution with zero manual configuration steps.<br>• CI/CD pipeline running build and automated tests on every push.<br>• Dynamic configuration injected strictly via environment variables.<br>• Meaningful health checks that detect actual service degradation.<br>• Structured logging and operational runbook. |
| **D — Data Science** | Rigorous decision modeling & economic trade-off analysis | • Formal operational definition of "needs a visit" with documented rejection of alternative definitions.<br>• Honest validation and explicit declaration of test blind spots.<br>• Uncertainty quantification (reporting performance ranges across gateway cohorts).<br>• Mathematical optimization of the €380 (false alarm) vs €600/week (missed outage) cost trade-off.<br>• Executive report and visualizations tailored to the Operations Manager. |
| **E — Machine Learning** | Train, evaluate, and interpret predictive models | • Model strictly outperforming `baseline_3sigma.py` on total operational cost.<br>• Feature importance, ablation analysis, and selection transparency.<br>• Adversarial validation: Out-of-time evaluation (future weeks) and out-of-distribution evaluation (unseen gateways).<br>• Resilience analysis under network topology and distribution shifts. |
| **F — MLOps** | Complete model lifecycle, versioning, and drift monitoring | • Decoupled training and inference pipelines with model artifact versioning.<br>• Deterministic inference (identical input + model version yields identical predictions).<br>• Streaming/batch data drift and schema change detection.<br>• Formal retraining policy and degradation alarms.<br>• Tested rollback procedure to previous model versions. |

### D. Evaluation & Marking Scheme

| Component | Weight | Assessment Scope |
|---|---|---|
| **Part 1 (Gate)** | **Pass / Fail** | Automated execution, schema validity of `predictions.csv`, completeness of artifacts. Failure halts evaluation immediately. |
| **Part 2 Specialization** | **60%** | Quality, depth, and engineering maturity within the single chosen discipline. |
| **Judgement & Critical Thinking** | **25%** | Scrutiny applied to data anomalies, questioning of problem ambiguities, defense of trade-offs. |
| **Communication & Synthesis** | **15%** | Clarity of `DECISIONS.md`, quality of the 6–8 min video recording, and business translation for operations stakeholders. |

### E. Submission & Data Restrictions
- **Repository**: Private GitHub repository during development; made public exactly at deadline (**Wednesday, 16 September 2026, 23:59 IST**).
- **Strict Data Prohibition**: The challenge data (104 MB) **MUST NOT** be committed to GitHub or published externally.
- **Commit History**: Must be clean and free of API keys, passwords, or raw data commits.

### F. Timeline & Deadlines (All Times IST)
- **Mon 24 Aug 2026**: Challenge release & Week 1 begins.
- **Wed 26 Aug 2026, 18:00 IST**: Round 1 clarification questions submission deadline.
- **Week 1 (recorded)**: Open live Q&A session (1 hour); answers distributed to all candidates.
- **Week 2**: Optional checkpoint push (unmarked smoke test).
- **Mon 07 Sep 2026, 18:00 IST**: Round 2 clarification questions submission deadline.
- **Week 3**: Round 2 answers distributed; no further questions accepted.
- **Wed 16 Sep 2026, 23:59 IST**: Final submission deadline.

### G. Live Session Format (35 Minutes)
Candidates who pass the submission review will undergo a 35-minute interactive technical interview:
1. **Unseen Data Execution**: Run the candidate's pipeline live on an unseen month of telemetry.
2. **Live Code Modification**: Implement a targeted live modification with LPDG engineers observing (e.g., handling a new data corruption mode, adjusting decision thresholds, adding an API route, or executing a model rollback).
3. **Strategic Roadmap Defense**: Defend what architectural enhancements an additional week of development would deliver.

---

## Section 2: Requirement Mapping Table

| Requirement | Exact Source | What It Means in Practice | Status |
|---|---|---|---|
| **Prediction Scope** | Brief p. 2, 7; Data Dict p. 6 | Exactly 8 Mondays (`2026-02-02` to `2026-03-23`), 15 gateways/week = 120 rows. | CONFIRMED BY LPDG |
| **Cost Matrix** | Brief p. 2–3 | €380 per technician visit (incurred whenever dispatched; wasted if no fault); €600 per week for every unvisited failing gateway (recurring weekly). | CONFIRMED BY LPDG |
| **Visit Capacity** | Brief p. 2–3 | 15 visits/week is a hard capacity ceiling, not a target or minimum. | CONFIRMED BY LPDG |
| **No-Model Allowance** | Brief p. 2 | Candidates in non-ML tracks (DevOps, Data Eng, Software Dev) may use `baseline_3sigma.py` as-is without penalty. | CONFIRMED BY LPDG |
| **Definition of "Needs a Visit"** | Brief p. 3 | LPDG intentionally refuses to provide a ground-truth formula; candidates must formulate and defend their own operational definition. | CONFIRMED BY LPDG (Intentional Open Design) |
| **Historical Data Cutoff** | Brief p. 2; Baseline code L50–51 | Predictions for a given Monday must strictly use data available prior to that Monday's timestamp (`< Monday 00:00:00 UTC`). | OBSERVED IN DATA & CONFIRMED BY CODE |
| **Evaluation Metric & Scoring Script** | Brief p. 3, 4 | LPDG evaluates candidates against an internal scoring script computing total operational cost, but the exact formula for identifying true/false failures during the scored period is undisclosed. | AMBIGUOUS / NEEDS CLARIFICATION |
| **Role of Expert Review Dataset** | Data Dict p. 5; `engineer_review_2026-02.xlsx` | 120 gateway assessments dated `2026-02-15` with 60 "Schlecht" and 60 "Normal". It is unclear whether this is an evaluation benchmark, training ground truth, or an operational simulation asset. | AMBIGUOUS / NEEDS CLARIFICATION |

---

## Section 3: Plain-Language Challenge Reconstruction (Phase 2)

### 1. What does LPDG operate?
LPDG operates a utility smart metering wireless communications network across several German states. The network collects consumption data from residential and commercial utility meters (electricity, gas, or water) and transmits it back to central utility billing and management systems.

### 2. What is a gateway?
A gateway is an edge telecommunications concentrator device installed on building rooftops, in basements, inside boiler/heating rooms (`Heizraum`), or on outdoor utility masts. Each gateway listens for wireless LoRa radio packets transmitted by 40 to 900 individual smart utility meters in its vicinity and relays this data back to LPDG over a cellular backhaul connection (e.g., 2G/3G/4G via Telekom, Vodafone, or O2).

### 3. What happens when a gateway fails?
Because utility meters transmit autonomously without loud acoustic or visual alarms, a failing gateway suffers **silent data loss**. The meters continue broadcasting, but their readings are no longer relayed to the backhaul. The failure produces no immediate network crash alarm; instead, it manifests gradually as missing meter readings, software reboot loops, or intermittent cellular disconnections.

### 4. Why does the failure matter?
When meter readings fail to arrive:
- Customers receive estimated or incorrect utility bills.
- Utility providers must dispatch manual meter readers at high operational expense.
- Undetected outages compound over time, leading to severe customer billing disputes and regulatory compliance penalties.

### 5. Why can only 15 gateways be visited per week?
Field technician teams have finite staffing, vehicle availability, and geographical travel constraints. The operations team has a hard logistical budget cap of 15 physical site inspections per calendar week.

### 6. What exactly must our system produce?
The system must generate an automated decision output: a single CSV file named `predictions.csv` containing exactly 15 ranked gateway identifiers for each of the 8 scored weeks, along with an operational score and an interpretable, human-readable justification (under 300 characters) explaining why each site was prioritized.

### 7. For which weeks?
For 8 consecutive Mondays in early 2026:
- Week 1: `2026-02-02`
- Week 2: `2026-02-09`
- Week 3: `2026-02-16`
- Week 4: `2026-02-23`
- Week 5: `2026-03-02`
- Week 6: `2026-03-09`
- Week 7: `2026-03-16`
- Week 8: `2026-03-23`

### 8. What does each prediction row mean?
Each row represents a physical dispatch order for one week:
- `week_start`: The Monday date when the dispatch schedule takes effect.
- `rank`: Priority integer from 1 (highest priority visit) to 15 (lowest priority visit).
- `gateway_id`: Unique hardware identifier of the targeted gateway.
- `score`: Quantitative ranking metric assigned by the algorithm.
- `reason`: Concise explanation for the operations manager summarizing the diagnostic signals triggering the visit.

### 9. What is Part 1?
Part 1 is the universal engineering baseline. It tests software hygiene, execution reliability, format adherence, critical thinking documentation, and communication skills. It is identical for all candidates.

### 10. What is Part 2?
Part 2 is the deep technical vertical where candidates demonstrate senior-level mastery in their chosen discipline (Data Engineering, Software Development, DevOps, Data Science, Machine Learning, or MLOps).

### 11. Why does LPDG say depth is more important than breadth?
LPDG wants to hire specialists who can build robust, production-grade solutions rather than superficial generalists who deliver half-finished prototypes across multiple domains. A single meticulously engineered pipeline or mathematically rigorous decision model beats multiple shallow implementations.

### 12. What does each discipline require?
- **Data Engineering**: Robust raw-to-clean ETL/ELT pipelines, idempotency, incremental partition processing, and schema validation.
- **Software Development**: Modular web API service, decoupling of business logic from transport, and comprehensive unit/integration/regression test suites.
- **DevOps**: Dockerized environment, environment-based configuration, automated CI workflows, health checks, and structured logging.
- **Data Science**: Mathematical modeling of economic trade-offs (€380 vs €600), operational definitions of failure, uncertainty quantification, and executive reporting.
- **Machine Learning**: Predictive modeling outperforming the baseline on cost, feature attribution, and rigorous out-of-time/out-of-distribution evaluation.
- **MLOps**: Decoupled training/inference pipelines, artifact versioning, deterministic reproducibility, drift detection, and automated rollback mechanisms.

### 13. How are candidates marked?
Evaluation follows a strict hierarchical rubric:
1. **Part 1 Gate**: Pass / Fail (mandatory prerequisite).
2. **Part 2 Technical Depth**: 60% of total score.
3. **Engineering Judgement & Defensibility**: 25% of total score.
4. **Communication & Business Translation**: 15% of total score.

### 14. What happens if Part 1 fails?
If `predictions.csv` is malformed, missing required columns, fails `validate_submission.py`, or cannot execute via a single command, the submission is rejected immediately. Part 2 is not evaluated.

### 15. What happens if a candidate is invited to the live session?
The candidate participates in a 35-minute live technical session where they run their pipeline on an unseen month of telemetry, perform a live code modification while LPDG engineers observe, and articulate their technical roadmap.
