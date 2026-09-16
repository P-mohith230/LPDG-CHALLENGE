# Candidate Round 1 Clarification Questions & Design Space Audit
**LPDG Innovation Hub Selection Challenge 2026**  
*Intentional Candidate Ownership vs Genuine Organizational Clarifications (Phases 9, 10, 12)*

---

## Section 1: Intentional Design Questions (Candidate Ownership — DO NOT ASK)

The Challenge Brief explicitly delegates several strategic, mathematical, and architectural decisions to the candidate. Asking LPDG about these areas will yield the official response: *"That is your call, tell us what you chose and why."*

### Delegated Decisions Catalogue:

1. **Definition of "Needs a Visit"**:
   - *Brief Citation (p. 3)*: *"We have not said what 'needs a visit' means... Those are yours to decide and yours to defend."*
   - *Candidate Ownership*: Formulating a domain-justified operational definition (e.g., persistent packet loss, consecutive watchdog reboots, prolonged backhaul disconnection, or severe meter read degradation).
2. **Decision Thresholds & False Alarm Tolerance**:
   - *Brief Citation (p. 3)*: *"We have not said how early is early enough, how many false alarms are acceptable, or which measure matters most."*
   - *Candidate Ownership*: Determining the quantitative sensitivity threshold that balances false dispatches against missed catastrophic failures.
3. **Choice of Track in Part 2**:
   - *Brief Citation (p. 2)*: *"Part 2 is one area you pick and go deep in. Which one you pick is part of what we read."*
   - *Candidate Ownership*: Selecting from Data Engineering, Software Development, DevOps, Data Science, Machine Learning, or MLOps based on individual strengths.
4. **Feature Engineering & Modeling Technique**:
   - *Brief Citation (p. 2, 4)*: Non-ML tracks may use the 3-sigma baseline; ML tracks must justify features fed vs omitted.
   - *Candidate Ownership*: Algorithm selection (XGBoost, Isolation Forests, LightGBM, heuristic rules) and feature creation.
5. **Economic Trade-Off Modeling**:
   - *Brief Citation (p. 4)*: *"Turn the €380 and €600 into an actual decision. Where do you draw the line, and what does moving it cost in each direction?"*
   - *Candidate Ownership*: Mathematical optimization of expected dispatch utility.

---

## Section 2: Genuine Clarifications for LPDG (Evaluation, Contracts, & Simulation)

The following 12 candidate questions target genuine operational ambiguities where clarification directly impacts architectural correctness and evaluation fairness:

---

### Candidate Question 1: Operational Definition and Temporal Availability of `engineer_review_2026-02.xlsx`
- **Question**: *In `engineer_review_2026-02.xlsx`, 120 gateways are reviewed as of 2026-02-15. For scoring weeks 1 and 2 (2026-02-02 and 2026-02-09), should candidates strictly withhold this file to prevent temporal leakage, or is it intended as a static offline validation benchmark across all weeks?*
- **Why It Matters**: Prevents accidental data leakage and clarifies whether the dataset represents a mid-simulation operational feed or an out-of-time evaluation target.
- **Source**: Data Dictionary p. 5 (`reviewed_on = 2026-02-15`); Brief p. 2.
- **Classification**: Genuine Clarification (Data Availability / Temporal Leakage).
- **Priority**: **HIGH**

---

### Candidate Question 2: Exact Mathematical Mechanics of Total Operational Cost Evaluation
- **Question**: *Regarding the €380 visit cost and €600/week unaddressed failure cost: When a failing gateway is visited in week $k$, does it incur €380 in week $k$ and €0 failure cost in subsequent weeks, and are ground-truth failures defined by subsequent technician outcomes, meter read deficits, or synthetic ground truth?*
- **Why It Matters**: For Data Science and Machine Learning candidates optimizing their loss functions or decision thresholds, knowing the exact simulation cost formula is critical for fair model comparison against the baseline.
- **Source**: Brief p. 2–3 ("What mistakes cost").
- **Classification**: Genuine Clarification (Evaluation / Scoring Script Contract).
- **Priority**: **HIGH**

---

### Candidate Question 3: Weekly Dispatch Persistence & Re-visit Policy
- **Question**: *If a gateway flagged in week $k$ is visited by technicians, does the operational simulation assume it is repaired and returned to a healthy baseline by week $k+1$, or can the same gateway be visited across consecutive weeks if telemetry remains degraded?*
- **Why It Matters**: Affects whether dispatch algorithms should apply a "cooling-off" filter suppressing recently visited gateways from immediate re-nomination.
- **Source**: Brief p. 2–3; `field_visits.csv`.
- **Classification**: Genuine Clarification (Operational Simulation Contract).
- **Priority**: **HIGH**

---

### Candidate Question 4: Handling Gateways Installed or Decommissioned During the Scored Period
- **Question**: *`gateway_master.csv` lists 12 decommissioned gateways and several gateways installed during early/mid 2026. Should our submission pipeline actively filter out gateways that were decommissioned prior to a given decision Monday?*
- **Why It Matters**: Ensures candidates do not recommend decommissioned assets for physical technician dispatches.
- **Source**: `gateway_master.csv` (`decommissioned_on`, `installed_on`).
- **Classification**: Genuine Clarification (Operational Filter Rule).
- **Priority**: **MEDIUM**

---

### Candidate Question 5: Evaluation of Gateway Ranking Order (Top 15 Ordering)
- **Question**: *In `predictions.csv`, does the scoring script evaluate the strict rank order (1 through 15) via rank-weighted metrics (like NDCG/Precision@K), or are all 15 visited gateways evaluated as an unweighted batch for that week?*
- **Why It Matters**: Dictates whether intra-week fine-ranking matters or if only top-15 set membership is evaluated.
- **Source**: Brief p. 2; `validate_submission.py` (L103–105).
- **Classification**: Genuine Clarification (Scoring Metric Mechanics).
- **Priority**: **MEDIUM**

---

### Candidate Question 6: Sub-15 Visit Allowance
- **Question**: *The brief states "Fifteen visits is a hard limit. Not a goal, not a minimum." If an algorithm determines that only 8 gateways require a visit in a given week, will `predictions.csv` with fewer than 15 rows per week be rejected by the automated grader, or must it always contain exactly 15 rows as enforced by `validate_submission.py`?*
- **Why It Matters**: Resolves a direct clash between the business brief ("not a minimum") and the validator script (`len(frame) == 120` hard requirement).
- **Source**: Brief p. 3 vs `validate_submission.py` L58–63.
- **Classification**: Genuine Clarification (Schema vs Business Requirement Contradiction).
- **Priority**: **HIGH**

---

### Candidate Question 7: Live Session Interface Contract
- **Question**: *For the live technical session where unseen data is provided, what exact format will the unseen partition take (e.g., a new `month=2026-04` Parquet partition in `data/telemetry`), and will external network access be available during the session?*
- **Why It Matters**: Crucial for container and pipeline configuration in DevOps and Data Engineering tracks.
- **Source**: Brief p. 4 ("If we invite you to a live session").
- **Classification**: Genuine Clarification (Live Assessment Environment).
- **Priority**: **MEDIUM**

---

### Candidate Question 8: Expected Evaluation of the `reason` Field
- **Question**: *Is the 300-character `reason` field in `predictions.csv` evaluated solely by human reviewers during Part 2 assessment, or is it parsed by automated NLP / regex scoring in the automated test harness?*
- **Why It Matters**: Clarifies whether reason strings must adhere to a strict programmatic template or can be natural language explanations for human operations managers.
- **Source**: Data Dictionary p. 6; `validate_submission.py` L92–98.
- **Classification**: Genuine Clarification (Grading Pipeline Mechanics).
- **Priority**: **MEDIUM**

---

### Candidate Question 9: Scope of Multi-Year Historical Work Orders (`field_visits.csv`)
- **Question**: *`field_visits.csv` contains work orders dating back to February 2025 (pre-dating the telemetry start in August 2025). Are candidates permitted to use the full historical visit log for prior fault probability modeling, provided events post-dating the decision Monday are masked?*
- **Why It Matters**: Confirms feature engineering boundary across historical work orders.
- **Source**: `field_visits.csv` (`requested_on` range `2025-02-03` to `2026-01-30`).
- **Classification**: Genuine Clarification (Feature Engineering Boundary).
- **Priority**: **LOW**

---

### Candidate Question 10: Units and Interpretation of Firmware Counter Overflows
- **Question**: *In telemetry, columns like `offline_duration_sec` and `avg_uptime` exhibit values far exceeding 3600 seconds/hour (e.g. >700,000s and >1.5B respectively). Can LPDG confirm whether these represent monotonically increasing cumulative firmware counters that reset on reboot, or raw uncalibrated register readings?*
- **Why It Matters**: Guides proper differencing and feature preprocessing in Data Engineering and ML tracks.
- **Source**: Data Dictionary p. 1; Observed distributions in Parquet data.
- **Classification**: Genuine Clarification (Data Engineering & Feature Calibration).
- **Priority**: **MEDIUM**
