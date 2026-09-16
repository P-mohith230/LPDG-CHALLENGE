# Project Decision Register
**LPDG Innovation Hub Selection Challenge 2026**  
*Structured Registry of Architectural, Statistical, Modeling, and Operational Choices*

---

## Purpose & Protocol
This register documents the 22 formal architectural and methodological decisions required for the project. In strict adherence to LPDG guidelines, decisions currently unresolved are cataloged as **`OPEN — REQUIRES INVESTIGATION`** until empirical evidence from the experiment backlog settles the choice. No candidate assumption is converted into a rule without experimental backing.

---

### D-01: Operational Definition of "Needs a Visit"
- **DECISION ID**: D-01
- **QUESTION**: What precise operational criteria define a gateway that genuinely "needs a visit"?
- **WHY IT MATTERS**: Forms the fundamental optimization objective. LPDG evaluates whether candidates can establish and defend this definition (25% Judgement).
- **OPTIONS**:
  1. Option A: Sustained meter reading collapse ($<50\%$ read success for 2+ weeks).
  2. Option B: Prolonged hardware blackout ($>48$ hours telemetry silence or power loss).
  3. Option C: Hybrid composite operational risk standard combining terminal silence, severe packet CRC corruption, and unrecoverable reboot loops.
- **EVIDENCE REQUIRED**: Cross-dataset correlation between telemetry precursors and confirmed technician repairs (`Fehler behoben`).
- **EXPERIMENT REQUIRED**: Experiment E-04 (Candidate Target Definitions Evaluation).
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 3 & 4 EVIDENCE [OBSERVED IN DATA]**:
  - Exp E-01 established that telemetry silence streaks $\ge 12\text{h}$ correlate with severe collection deficits ($<50\%$ read ratio), inflecting severe deficit probability to $54.97\%$ (and $77.50\%$ for $\ge 24\text{h}$).
  - Exp E-03 established an empirical non-linear transfer function for backhaul downtime: weekly offline hours $>24\text{h}$ increase severe deficit probability from $<0.2\%$ to $7.56\%$, jumping to $30.23\%$ for $>72\text{h}$ and $77.32\%$ for $>168\text{h}$.
  - Exp E-04 confirmed that confirmed repairs (`Fehler behoben`) have $5.41\times$ higher trailing reboots and $13.44\times$ higher power cycles than no-fault visits, but $70.2\%$ of repaired gateways had $\le 10$ reboots. 60.7% of evaluated field visits were recorded as `Kein Fehler gefunden`, demonstrating substantial outcome ambiguity/noise in the historical visit dataset. Field visits are noisy operational proxies rather than ground truth [REASONABLE INFERENCE supported by observed overlap].
  - Stage 4 cross-target analysis proved that 99.5% of severe collection deficits co-occur with physical electrical/backhaul degradation (Target C strict composite overlap).
- **FINAL DECISION**: A gateway genuinely "needs a visit" when it experiences a severe smart-meter collection deficit ($\text{read\_ratio} < 0.50$) driven by physical, electrical, or backhaul failure.
- **REASON**: Directly aligns with the utility's core SLA and regulatory penalty risk. When collection drops below 50%, meter buffer capacity saturates within 24–72 hours, permanently compromising billing intervals.
- **REJECTED ALTERNATIVE**:
  - Rejected binary zero-reads ($N=2$, $0.03\%$): statistically degenerated.
  - Rejected minor deficit ($<80\%$, $17.66\%$): captures routine transient RF fades that self-heal without physical dispatches.
  - Rejected technician visit logs alone: 60.7% outcome ambiguity and crew budget rate-limiting.
- **COST / RISK**: Too narrow a definition misses €600 outages; too broad triggers €380 false alarm dispatches.
- **SOURCE**: Brief p. 3, FAQ Round 1 §4.1, FAQ Round 2 §5.1, §8

---

### D-02: Fault-Target Construction for Supervised Learning
- **DECISION ID**: D-02
- **QUESTION**: How should binary/continuous training targets be synthesized from future historical telemetry without leakage?
- **WHY IT MATTERS**: Dictates what the supervised model learns to predict. Must avoid target leakage into features for the same week.
- **OPTIONS**:
  1. Option A: Binary indicator of whether the gateway suffers $\ge 48$ hours silence in week $k+1$.
  2. Option B: Binary indicator of whether meter read deficit exceeds 50% in week $k+1$.
  3. Option C: Multi-task failure score combining backhaul failure, power cycle reboots, and CRC corruption.
- **EVIDENCE REQUIRED**: Label distribution, class balance, and stability across August 2025 – January 2026.
- **EXPERIMENT REQUIRED**: Experiment E-04 & E-06.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 3 & 4 EVIDENCE [OBSERVED IN DATA]**:
  - `meters_read == 0` occurred exactly 2 times across 7,226 historical gateway-weeks ($0.03\%$), ruling out binary zero-reads as a viable standalone supervised learning target.
  - Champion Target A1 (`read_ratio < 0.50` at week $k+1$) occurred in 551 of 6,927 valid pairs ($7.95\%$), affecting 106 unique gateways, with steady monthly prevalence ($7.32\%$ in Aug 2025 to $8.10\%$ in Jan 2026, monthly std = $0.90\%$).
  - Target B (telemetry silence $\ge 24\text{h}$) has $31.28\%$ prevalence and high monthly variance ($9.14\%$).
  - Target D (field repair) has only $1.65\%$ prevalence ($N=114$) due to crew budget rate-limiting.
- **FINAL DECISION**: Synthesize binary supervised learning target $Y_{g, k+1} = \mathbb{I}(\text{read\_ratio}_{g, k+1} < 0.50)$ over a 1-week forward horizon (Monday 00:00:00 UTC to Sunday 23:59:59 UTC of week $k+1$).
- **REASON**: Provides stable, non-degenerated class balance ($7.95\%$), exceptional monthly temporal stability ($0.90\%$ std), direct alignment with €600 penalty risks, and complete isolation from lagged features ($t < \text{Monday}$).
- **REJECTED ALTERNATIVE**:
  - Rejected Option A (binary zero-reads): extreme class sparsity ($N=2$).
  - Rejected Option C (direct field visit classification): severe selection bias and 60.7% no-fault noise.
- **COST / RISK**: Target leakage causes artificial 100% training accuracy but immediate failure on unseen live data. Protected by programmatic leakage firewall.
- **SOURCE**: FAQ Round 1 §6.13, FAQ Round 2 §4.5

---

### D-03: ML Prediction Horizon and Lead Time
- **DECISION ID**: D-03
- **QUESTION**: What lead-time horizon should features evaluate prior to decision Monday?
- **WHY IT MATTERS**: Early detection compounds €600 weekly savings, but premature prediction increases false positive noise.
- **OPTIONS**:
  1. Option A: Immediate trailing 24 hours ($T-24	ext{h}$).
  2. Option B: Trailing 7 days ($T-7	ext{d}$, matching baseline).
  3. Option C: Hierarchical multi-resolution window ($T-24	ext{h}$, $T-7	ext{d}$, $T-28	ext{d}$).
- **EVIDENCE REQUIRED**: Degradation curves prior to historical failure events.
- **EXPERIMENT REQUIRED**: Experiment E-06 (Lead-Time Sensitivity Analysis).
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Pending Experiment E-06.
- **REASON**: Pending.
- **REJECTED ALTERNATIVE**: Pending.
- **COST / RISK**: Missing the early detection window reduces counterfactual cost savings.
- **SOURCE**: FAQ Round 1 §5.2, FAQ Round 2 §3.5, §8

---

### D-04: Handling Telemetry Silence (Absent Rows)
- **DECISION ID**: D-04
- **QUESTION**: How should missing hourly telemetry records be represented and scored?
- **WHY IT MATTERS**: Silence has multiple causes; absent records are omitted rows in Parquet, not zero values.
- **OPTIONS**:
  1. Option A: Complete time-grid reindexing and explicit silence duration counting.
  2. Option B: Imputing zeros across all missing timestamps.
  3. Option C: Dropping gateways with missing hours from ranking consideration.
- **EVIDENCE REQUIRED**: Empirical frequency and duration of timestamp gaps across gateways.
- **EXPERIMENT REQUIRED**: Experiment E-01 (Telemetry Silence Profiling).
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION (Option A Empirically Supported)
- **STAGE 3 EVIDENCE [OBSERVED IN DATA — Exp E-01]**:
  - 1–3h silence spells occur in $81.62\%$ of gateway-weeks as baseline reporting jitter (severe deficit rate $1.27\%$).
  - Streaks $\ge 12\text{h}$ inflect severe deficit probability to $54.97\%$, and tail silence $\ge 24\text{h}$ has $94.44\%$ next-week deficit rate.
  - Telemetry silence (omitted rows) and offline duration share only $37\%$ common variance ($r = +0.6116$), proving they capture complementary physical outage states.
- **FINAL DECISION**: Option A (Time-grid reindexing and explicit silence streak/tail duration counting).
- **REASON**: Explicit spell and streak tracking cleanly isolates genuine operational outages from baseline transmission jitter without data distortion.
- **REJECTED ALTERNATIVE**: Option B (imputing zeros across omitted rows) masks power outages; Option C (dropping silent gateways) blinds model to failing devices.
- **COST / RISK**: Dropping silent gateways misses catastrophic power-off outages; naive zero-fill masks downtime.
- **SOURCE**: FAQ Round 1 §4.6, FAQ Round 2 §3.4, §8

---

### D-05: Handling Incomplete Telemetry per Gateway
- **DECISION ID**: D-05
- **QUESTION**: Should gateways reporting fewer than 168 hours in a trailing week be penalized, normalized, or excluded?
- **WHY IT MATTERS**: Compares gateways with 2 reporting hours against gateways with 168 reporting hours.
- **OPTIONS**:
  1. Option A: Compute rate-based intensities (e.g. `reboots_per_reporting_hour`) with confidence weighting.
  2. Option B: Exclude any gateway reporting $<24$ hours in a week.
  3. Option C: Treat missing hours as offline duration.
- **EVIDENCE REQUIRED**: Distribution of reporting hours across active vs. degraded gateways.
- **EXPERIMENT REQUIRED**: Experiment E-05 (Missing Data Handling Impact).
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Pending Experiment E-05.
- **REASON**: Pending.
- **REJECTED ALTERNATIVE**: Pending.
- **COST / RISK**: Excluding incomplete gateways blinds the system to devices dying mid-week.
- **SOURCE**: FAQ Round 2 §3.7

---

### D-06: Missing-Value Imputation Policy
- **DECISION ID**: D-06
- **QUESTION**: What imputation strategy should be applied across the 57 telemetry columns?
- **WHY IT MATTERS**: Blanket `fillna(0)` across 50+ columns is an unconsidered decision (FAQ §3.2).
- **OPTIONS**:
  1. Option A: Domain-specific per-column imputation (e.g. 0 for counts, forward-fill for firmware version, median for load).
  2. Option B: Global mean imputation.
  3. Option C: Complete-case row deletion.
- **EVIDENCE REQUIRED**: Null value audit per column in Parquet partitions.
- **EXPERIMENT REQUIRED**: Experiment E-05.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Domain-specific per-column imputation mapping.
- **REASON**: Respects physical measurement units and firmware counter properties.
- **REJECTED ALTERNATIVE**: Global `fillna(0)` or global mean imputation.
- **COST / RISK**: Erroneous imputation distorts statistical anomalies.
- **SOURCE**: FAQ Round 2 §3.2

---

### D-07: Recent-vs-Historical Weighting Scheme
- **DECISION ID**: D-07
- **QUESTION**: What decay or weighting function should be applied to recent hours vs. historical baselines?
- **WHY IT MATTERS**: Balances rapid detection against transient noise volatility.
- **OPTIONS**:
  1. Option A: Uniform trailing 7-day boxcar window (baseline approach).
  2. Option B: Exponential time-decay kernel emphasizing the last 24–48 hours.
  3. Option C: Ratio of 24-hour rate to 28-day baseline rate.
- **EVIDENCE REQUIRED**: Signal-to-noise ratio of recent load and disconnection spikes.
- **EXPERIMENT REQUIRED**: Experiment E-06.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Pending Experiment E-06.
- **REASON**: Pending.
- **REJECTED ALTERNATIVE**: Pending.
- **COST / RISK**: Over-weighting recent noise induces false alarms; under-weighting delays detection.
- **SOURCE**: FAQ Round 2 §3.5

---

### D-08: Feature Selection & Dimensionality Reduction
- **DECISION ID**: D-08
- **QUESTION**: Which subset of the 57 telemetry columns and asset metadata should enter the model?
- **WHY IT MATTERS**: Zero-variance columns add noise; collinear features destabilize tree attributions.
- **OPTIONS**:
  1. Option A: All 57 raw features.
  2. Option B: Filtered set removing zero-variance operator columns, dropping uninformative CRC ratio / raw packet counts, and focusing on verified physical clusters (Cellular RSSI, Transmit Success, Power Reboots, Non-linear Offline Duration, Tail Silence).
  3. Option C: PCA / Latent factor embeddings.
- **EVIDENCE REQUIRED**: Feature correlation matrix, SHAP importance, zero-variance audit, and Exp E-05 radio forensics.
- **EXPERIMENT REQUIRED**: Experiment E-05 & E-08.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION (Option B Empirically Supported)
- **STAGE 3 EVIDENCE [OBSERVED IN DATA — Exp E-05]**:
  - CRC error count is $100.0\%$ collinear with total packets ($R = 1.0000$), and `crc_ratio` is saturated at $\approx 1.0$ with zero correlation to collection deficits ($r = -0.0335$); rejected as a standalone failure predictor.
  - Raw packet volume is heavily confounded by antenna gain (Yagi 9dBi averages 389,623 pkts/week vs 4,694 for Omni 3dBi); rejected as a raw predictor.
  - Cellular `rssi_bad` ($r = -0.2827$ with read ratio, $+0.2290$ with severe deficit) and downlink `tx_success` ($r = +0.2031$) carry genuine predictive signal.
- **FINAL DECISION**: Pruned physical feature set (removing 7 zero-variance operators, excluding unconditioned CRC ratio and raw packet volume).
- **REASON**: Eliminates uninformative noise parameters and prevents antenna confounding.
- **REJECTED ALTERNATIVE**: Retaining all 57 raw columns uninspected or treating CRC ratio as a failure indicator.
- **COST / RISK**: Dropping a subtle failure indicator increases missed fault penalties.
- **SOURCE**: FAQ Round 2 §2.4, Brief p. 4

---

### D-09: Model Architecture Selection
- **DECISION ID**: D-09
- **QUESTION**: Which algorithmic family should generate the weekly gateway ranking?
- **WHY IT MATTERS**: Must execute offline in seconds, provide interpretable reason strings, and be modifiable live under observation.
- **OPTIONS**:
  1. Option A: Gradient Boosted Trees (LightGBM / XGBoost).
  2. Option B: Statistical Hazard / Survival Regression (Cox Proportional Hazards).
  3. Option C: Multi-criteria Risk Scoring Heuristic with Calibrated Thresholds.
- **EVIDENCE REQUIRED**: Offline cost comparison against `baseline_3sigma.py`.
- **EXPERIMENT REQUIRED**: Experiment E-11 (Model Benchmark vs. Baseline).
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Pending benchmark execution.
- **REASON**: Pending.
- **REJECTED ALTERNATIVE**: Pending.
- **COST / RISK**: Complex deep learning models cannot be modified live in 10 minutes and risk gate failure.
- **SOURCE**: FAQ Round 2 §5.3, §7.2, Brief p. 4

---

### D-10: Master Validation Strategy
- **DECISION ID**: D-10
- **QUESTION**: How should validation splits be constructed to ensure findings survive sceptical review?
- **WHY IT MATTERS**: Sceptic-proof validation is the central test of the 25% Judgement component (FAQ §5.2).
- **OPTIONS**:
  1. Option A: Random hourly train/test split.
  2. Option B: Device-disjoint (grouped by gateway) AND forward-in-time (expanding temporal window).
  3. Option C: Standard K-fold cross validation.
- **EVIDENCE REQUIRED**: Demonstration of fold-to-fold stability and out-of-time evaluation.
- **EXPERIMENT REQUIRED**: Experiment E-12 & E-13.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 7 EVIDENCE [OBSERVED IN DATA]**:
  - Temporal walk-forward evaluation across Nov 2025, Dec 2025, and Jan 2026 proved model stability across real-world distribution drift (ROC-AUC 0.9680–0.9742).
  - 5-Fold gateway-disjoint evaluation proved zero gateway overlap and consistent generalization to unseen hardware (ROC-AUC 0.9407–0.9603).
- **FINAL DECISION**: Dual-Dimension Validation: Forward-Time Walk-Forward Validation + Gateway-Disjoint GroupKFold Validation.
- **REASON**: Mandated by Brief p. 4 and FAQ Round 2 §5.2, §6.9. Evaluates temporal drift and unseen hardware independently.
- **REJECTED ALTERNATIVE**: Random shuffling of gateway-weeks (severely contaminates time and hardware).
- **COST / RISK**: Overfitting to known devices creates false confidence.
- **SOURCE**: FAQ Round 2 §5.2, §6.9

---

### D-11: Gateway-Disjoint Split Mechanics
- **DECISION ID**: D-11
- **QUESTION**: How should gateways be grouped to test generalization to unseen devices?
- **WHY IT MATTERS**: In live evaluation, new gateways may be introduced; models must not memorize device IDs.
- **OPTIONS**:
  1. Option A: 5-Fold GroupKFold on `gateway_id`.
  2. Option B: Random 80/20 gateway holdout.
  3. Option C: Stratification by `n_meters_installed`.
- **EVIDENCE REQUIRED**: Verification that no gateway ID appears in both train and test splits.
- **EXPERIMENT REQUIRED**: Experiment E-12.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 7 EVIDENCE [OBSERVED IN DATA]**:
  - Implemented in `src/evaluation/splitters.py` via `GroupKFold(n_splits=5)`.
  - Zero gateway overlap verified programmatically across all 5 folds.
  - Champion model achieved mean ROC-AUC of 0.9521 on completely unseen hardware.
- **FINAL DECISION**: 5-Fold GroupKFold grouped strictly by normalized bare `gateway_id`.
- **REASON**: Enforces complete device isolation and tests pure hardware generalization.
- **REJECTED ALTERNATIVE**: Simple random partitioning without device grouping.
- **COST / RISK**: Identity memorization is completely eliminated.
- **SOURCE**: FAQ Round 2 §5.2

---

### D-12: Forward-Time Temporal Split Mechanics
- **DECISION ID**: D-12
- **QUESTION**: What temporal horizon should be held out for final pre-submission out-of-time validation?
- **WHY IT MATTERS**: Simulates the exact operational task (predicting upcoming weeks from past data).
- **OPTIONS**:
  1. Option A: Train on Aug–Nov 2025; Test on Dec 2025 – Jan 2026.
  2. Option B: Train on Aug–Dec 2025; Test on Jan 2026.
  3. Option C: Expanding walk-forward monthly splits (Fold 1: Nov, Fold 2: Dec, Fold 3: Jan).
- **EVIDENCE REQUIRED**: Temporal stability of feature distributions and out-of-time cost reduction.
- **EXPERIMENT REQUIRED**: Experiment E-13.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 7 EVIDENCE [OBSERVED IN DATA]**:
  - Fold 1 (Nov 2025 Val): €48,000 cost, 45.0% Precision@15, 60.75% Recall.
  - Fold 2 (Dec 2025 Val): €56,100 cost, 37.33% Precision@15, 54.90% Recall.
  - Fold 3 (Jan 2026 Val): €39,000 cost, 36.67% Precision@15, 70.65% Recall.
- **FINAL DECISION**: Expanding Walk-Forward Temporal Split schedule across November 2025, December 2025, and January 2026.
- **REASON**: Mimics weekly decision cadence and confirms performance directly prior to the scored February 2026 window.
- **REJECTED ALTERNATIVE**: Static train/test split.
- **COST / RISK**: Single static split hides temporal volatility.
- **SOURCE**: FAQ Round 2 §5.2, §6.9

---

### D-13: Offline Cost Function Implementation
- **DECISION ID**: D-13
- **QUESTION**: How should the official cost accounting be codified in code?
- **WHY IT MATTERS**: Evaluation script assesses total cost: €380 fixed visit + €600/week unaddressed fault per episode.
- **OPTIONS**:
  1. Option A: Static weekly penalty lookup without episode tracking.
  2. Option B: Dynamic multi-week episode simulator tracking earliest visit and stopping accrual.
  3. Option C: Precision@15 proxy metric.
- **EVIDENCE REQUIRED**: Exact match with FAQ §4.1 and §5.2 cost examples.
- **EXPERIMENT REQUIRED**: Experiment E-10.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 6 EVIDENCE [OBSERVED IN DATA]**:
  - Implemented in `src/evaluation/cost_simulator.py` (`simulate_operational_cost`).
  - Unit-tested multi-week episode interruption, penalty accrual termination, and repeat-visit waste accounting (`tests/test_stage6.py`).
  - Successfully benchmarked Baseline 3-Sigma (€206,700) and Random Dispatch (€357,300).
- **FINAL DECISION**: Dynamic Multi-Week Episode Cost Simulator strictly following FAQ Round 2 §4.1 rules.
- **REASON**: Retrospective evaluation requires exact modeling of unaddressed fault weeks and repeat visit penalties.
- **REJECTED ALTERNATIVE**: Simple confusion matrix metrics (F1/AUC) which ignore episode duration dynamics.
- **COST / RISK**: Isolated behind strict evaluation firewall to prevent test-set contamination.
- **SOURCE**: FAQ Round 2 §4.1, §5.1, §5.2

---

### D-14: Economic Threshold Calibration
- **DECISION ID**: D-14
- **QUESTION**: At what predicted failure probability / score should the operational cutoff be placed?
- **WHY IT MATTERS**: Connects €380 and €600 into an actual decision (Data Science marking criterion #4).
- **OPTIONS**:
  1. Option A: Fixed rank cutoff (top 15 always dispatched regardless of score).
  2. Option B: Dual policy: Top 15 ranked in `predictions.csv`, but internal threshold $	au^*$ identifies sub-15 cutoff documented in `DECISIONS.md`.
  3. Option C: Fixed probability cutoff $	au = 0.5$.
- **EVIDENCE REQUIRED**: Parametric sweep of $	au \in [0.1, 0.9]$ against total cost.
- **EXPERIMENT REQUIRED**: Experiment E-09 (Threshold vs. Operational Cost Curve).
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Dual Policy: Full 15-rank submission + explicit operational threshold $	au^*$ in `DECISIONS.md`.
- **REASON**: Complies with 120-row validator contract while satisfying economic threshold requirement.
- **REJECTED ALTERNATIVE**: Submitting $<15$ rows (violates validator).
- **COST / RISK**: Wasting slots on healthy gateways when fleet is healthy.
- **SOURCE**: FAQ Round 1 §3.4, FAQ Round 2 §5.1

---

### D-15: Re-visit & Cooldown Policy
- **DECISION ID**: D-15
- **QUESTION**: How should previously visited gateways be handled in subsequent weeks?
- **WHY IT MATTERS**: Re-picking within the same episode costs €380, burns a slot, and saves €0 (FAQ §4.1).
- **OPTIONS**:
  1. Option A: Stateless (gateways evaluated independently each week; duplicates permitted).
  2. Option B: Fixed $K$-week cooldown suppression filter (e.g. cannot re-visit for 1, 2, or 3 weeks).
  3. Option C: Adaptive re-visit filter (suppress unless a new distinct failure signature emerges).
- **EVIDENCE REQUIRED**: Cost simulation comparing stateless vs. cooldown dispatch policies.
- **EXPERIMENT REQUIRED**: Experiment E-10 (Revisit Policy Impact).
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 8 & AUDIT EVIDENCE [OBSERVED IN DATA]**:
  - Evaluated on unified 16-week evaluation window (`2025-10-06` to `2026-01-19`, 240 dispatches):
    - Cooldown = 0 weeks (Stateless): Total Cost = €172,200 (125 repeat visits, 63.71% Recall).
    - Cooldown = 1 week: Total Cost = €139,800 (87 repeat visits, 78.23% Recall).
    - Cooldown = 2 weeks: Total Cost = **€128,400** (52 repeat visits, **83.33% Recall**; saves **€43,800** over stateless ranking and **€36,000** over official 3-sigma baseline).
    - Cooldown = 3 weeks: Total Cost = €129,000 (35 repeat visits, 83.06% Recall; over-suppresses gateways experiencing legitimate new independent episodes).
- **FINAL DECISION**: Fixed 2-Week Cooldown Suppression Filter.
- **REASON**: Empirically minimizes operational cost by cutting 73 redundant repeat visits, freeing dispatch capacity to capture newly emerging unvisited faults, lifting fleet recall from 63.71% to 83.33%.
- **REJECTED ALTERNATIVE**:
  - Stateless ranking (costs €43,800 more due to repeat visits).
  - 3-week cooldown (over-suppression raises penalty costs by €600).
- **COST / RISK**: Too long a cooldown risks missing legitimate repeat episodes; 2 weeks matches the empirical mean episode resolution duration.
- **SOURCE**: FAQ Round 2 §4.1

---

### D-17: Offline Duration Feature Semantics & Peak Event Bounding
- **DECISION ID**: D-17
- **QUESTION**: How should `offline_duration_sec` and `disconnection_cnt` be aggregated across hourly telemetry observations?
- **WHY IT MATTERS**: Telemetry audit revealed that `offline_duration_sec` is a frozen/cached register snapshot of the last event duration, not an incremental counter. Naive hourly summation duplicates identical duration values across consecutive packets, producing physically impossible explanations (e.g. 3,901.5h in a 168h week).
- **OPTIONS**:
  1. Option A: Naive hourly summation (`sum()`).
  2. Option B: Peak event duration bounded by wall-clock observation window (`min(168.0, max() / 3600.0)`).
  3. Option C: Delete offline duration feature entirely.
- **EVIDENCE REQUIRED**: Cross-correlation with severe collection deficits, empirical packet repetition analysis, physical upper bound verification.
- **CURRENT STATUS**: SETTLED [OBSERVED IN DATA]
- **AUDIT EVIDENCE**:
  - Telemetry inspection of hanging gateways (`02C0F45F31E7`, `0AC437023B18`) proved identical disconnection durations (e.g. 726,642s) repeated across dozens of consecutive packets.
  - Peak weekly disconnection duration exhibits higher correlation with next-week severe collection deficit (0.65–0.71) than naive summation (0.51–0.58).
  - Feature ablation confirmed removing offline features reduces PR-AUC from 0.7759 to 0.7559.
- **FINAL DECISION**: Bounded Peak Event Duration (`feat_offline_hours = min(168.0, max(offline_duration_sec) / 3600.0)`).
- **REASON**: Enforces strict physical upper bound ($0 \le \text{hours} \le 168.0$), eliminates impossible reason string values, and enhances predictive fidelity.
- **REJECTED ALTERNATIVES**:
  - Naive sum: Violates physics, corrupts reason builder, lowers predictive correlation.
  - Complete deletion: Discards valuable backhaul distress signal.

---

### D-18: German Site Type Mapping & Distinct Observed Hours Invariant
- **DECISION ID**: D-18
- **QUESTION**: How should categorical metadata and telemetry observation hours be represented?
- **WHY IT MATTERS**: `gateway_master.csv` records site types in German (`Gebäude`, `Heizraum`, `Kellerraum`, `Außenmast`, `Schaltschrank`), which produced 100% constant zero features under English substring checks. Additionally, retransmitted packet rows caused raw packet counts to exceed 168h (up to 177h).
- **OPTIONS**:
  1. Option A: Leave as raw substrings and raw packet counts.
  2. Option B: Explicitly map German categories to installation types, and enforce distinct hourly floor set for observed hours ($O + M = 168$).
- **CURRENT STATUS**: SETTLED [OBSERVED IN DATA]
- **FINAL DECISION**: Semantic German mapping for site indicators and hourly conservation law ($O + M = 168$) for telemetry coverage.
- **REASON**: Restores feature variance to site categories (70.5% indoor, 29.5% outdoor, 16.0% pole) and guarantees mathematically sound telemetry availability metrics.

---

### D-16: Deterministic Secondary Tie-Breaking
- **DECISION ID**: D-16
- **QUESTION**: What secondary key should guarantee identical ranking output across identical inputs?
- **WHY IT MATTERS**: Non-deterministic tie-breaking violates MLOps requirements and is penalized during live sessions.
- **OPTIONS**:
  1. Option A: Primary sort on `risk_score` descending; Secondary sort on normalized bare `gateway_id` ascending.
  2. Option B: Arbitrary DataFrame row index order.
  3. Option C: Random tie-breaking.
- **EVIDENCE REQUIRED**: Verification of byte-identical predictions across repeated runs.
- **EXPERIMENT REQUIRED**: Experiment E-11 & Stage 9 reproducibility test.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 8 & 9 EVIDENCE [OBSERVED IN DATA]**:
  - Implemented in `rank_gateways_for_week` as `.sort_values(["risk_score", "gateway_id"], ascending=[False, True])`.
  - Byte-for-byte identical output verified programmatically in `tests/test_stage9.py` (`test_clean_machine_reproducibility`).
- **FINAL DECISION**: Strict Deterministic Composite Sort: `(-risk_score, gateway_id)`.
- **REASON**: Guarantees 100% reproducibility, eliminates arbitrary dataframe ordering, and complies with MLOps requirements.
- **REJECTED ALTERNATIVE**: Index-based sorting (fails reproducibility across different environments or sharded engines).
- **COST / RISK**: None. Fully deterministic.
- **SOURCE**: FAQ Round 2 §3.6, §6.9

---

### D-17: Operational Reason Generation Template
- **DECISION ID**: D-17
- **QUESTION**: How should the human-readable `reason` string ($\le 300$ chars) be generated?
- **WHY IT MATTERS**: First thing human operations managers review. Must be actionable diagnostic prose.
- **OPTIONS**:
  1. Option A: Dynamic templating inserting dominant feature breaches, hours degraded, and connected meters.
  2. Option B: Static generic reason string across all rows.
  3. Option C: Raw feature vector dump.
- **EVIDENCE REQUIRED**: Review of reason string lengths ($\le 300$ chars) and operational readability.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **STAGE 8 & 9 EVIDENCE [OBSERVED IN DATA]**:
  - Implemented in `src/prediction/reason_builder.py` (`build_dispatch_reason`).
  - Evaluates telemetry silence, offline duration, disconnections, power cycles, and high-impact hub status.
  - Strictly asserted $\le 300$ chars in unit tests and official `validate_submission.py` (0 violations across all 120 submission rows).
- **FINAL DECISION**: Structured Evidence-Grounded Diagnostic Template.
- **REASON**: Directly communicates operational risk to field dispatchers using pre-decision telemetry facts without speculation.
- **REJECTED ALTERNATIVE**: Static boilerplate or raw JSON vector dump.
- **COST / RISK**: Non-compliant if length > 300 chars. Programmatically guarded.
- **SOURCE**: FAQ Round 1 §3.5, FAQ Round 2 §5.3

---

### D-18: Model Versioning & Local Serialization
- **DECISION ID**: D-18
- **QUESTION**: What format and naming scheme should be used for model artifacts?
- **WHY IT MATTERS**: Must be committed to git, run offline, and support rollback demonstrations.
- **OPTIONS**:
  1. Option A: Serialized `.joblib` / `.pkl` model artifact paired with JSON metadata (`model_v1.0.json`).
  2. Option B: Cloud-hosted model registry (MLflow / Weights & Biases).
  3. Option C: Training inline upon execution.
- **EVIDENCE REQUIRED**: Artifact file size verification ($<2	ext{ MB}$).
- **EXPERIMENT REQUIRED**: Offline loading test without internet connectivity.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Local versioned `.joblib` model artifact with explicit JSON schema and parameter manifest.
- **REASON**: Complies with offline constraint and satisfies MLOps criteria.
- **REJECTED ALTERNATIVE**: Cloud registry requiring runtime network tokens.
- **COST / RISK**: Disqualification if runtime requires internet download.
- **SOURCE**: FAQ Round 2 §2.2, §6.10, §6.11

---

### D-19: Training vs. Inference Decoupling
- **DECISION ID**: D-19
- **QUESTION**: How should training code be separated from the prediction pipeline?
- **WHY IT MATTERS**: Retraining during live evaluation will exceed the 35-minute session limit.
- **OPTIONS**:
  1. Option A: Fully separate scripts: `src/train.py` (offline training) and `src/predict.py` (fast inference).
  2. Option B: Single monolithic script that trains and predicts on every run.
  3. Option C: Jupyter notebook execution.
- **EVIDENCE REQUIRED**: Benchmark runtime of `src/predict.py` ($<30	ext{ seconds}$).
- **EXPERIMENT REQUIRED**: Runtime profiling test.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Decoupled `src/train.py` and `src/predict.py`.
- **REASON**: Fast, robust execution during evaluation.
- **REJECTED ALTERNATIVE**: Monolithic train-on-predict execution.
- **COST / RISK**: Runtime timeout during live evaluation.
- **SOURCE**: FAQ Round 1 §2.4, FAQ Round 2 §7.2

---

### D-20: Model Retraining Policy
- **DECISION ID**: D-20
- **QUESTION**: What operational triggers dictate when a production model should be retrained?
- **WHY IT MATTERS**: Explicit MLOps bullet point requirement.
- **OPTIONS**:
  1. Option A: Cadence-based: Retrain monthly upon receipt of new verified meter reading batches.
  2. Option B: Drift-based: Retrain when feature distribution divergence exceeds Wasserstein distance threshold.
  3. Option C: Combined cadence and performance degradation trigger.
- **EVIDENCE REQUIRED**: Documented rule in `DECISIONS.md`.
- **EXPERIMENT REQUIRED**: Simulated retraining trigger test.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Monthly cadence triggered by new meter-read validation batches, supplemented by data drift alarms.
- **REASON**: Reflects real-world utility billing and maintenance cycles.
- **REJECTED ALTERNATIVE**: Continuous retraining on unverified streaming telemetry.
- **COST / RISK**: Retraining on corrupted data degrades model quality.
- **SOURCE**: Brief p. 4 (Track F), FAQ Round 1 §2.4

---

### D-21: Incoming Data Drift & Schema Monitoring
- **DECISION ID**: D-21
- **QUESTION**: How will the service detect if incoming live data changes schema, scale, or distribution?
- **WHY IT MATTERS**: MLOps bullet requirement and live-session readiness check.
- **OPTIONS**:
  1. Option A: Schema validation assertions checking expected columns, datatypes, and null rate bounds.
  2. Option B: Statistical Kolmogorov-Smirnov / Population Stability Index (PSI) tests on incoming features.
  3. Option C: No monitoring.
- **EVIDENCE REQUIRED**: Test asserting detection of corrupted/malformed input partitions.
- **EXPERIMENT REQUIRED**: Unit test `test_schema_drift_detection`.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Lightweight schema assertion contract checking column existence, non-nullity, and range validity.
- **REASON**: Fails fast with clear operational alerts rather than silently producing wrong predictions.
- **REJECTED ALTERNATIVE**: Silent imputation without alarming.
- **COST / RISK**: Pipeline silently outputs junk predictions on corrupted data.
- **SOURCE**: Brief p. 4, FAQ Round 2 §6.11, §7.1

---

### D-22: Final Repository Deployment Structure
- **DECISION ID**: D-22
- **QUESTION**: What deployment wrapper will provide the one-command interface for external evaluation?
- **WHY IT MATTERS**: Single command on a clean machine is the primary Part 1 gate.
- **OPTIONS**:
  1. Option A: Docker Compose mounting `./data` volume (`docker compose up`).
  2. Option B: Root shell script (`./run.sh`) with standard Python virtual environment.
  3. Option C: Dual support: Docker Compose + fallback `./run.sh` script.
- **EVIDENCE REQUIRED**: Rehearsal on a clean VM / foreign environment.
- **EXPERIMENT REQUIRED**: End-to-end smoke test execution.
- **CURRENT STATUS**: OPEN — REQUIRES INVESTIGATION
- **FINAL DECISION**: Dual support: Primary Docker Compose + local `./run.sh` entrypoint.
- **REASON**: Maximum portability across Linux, macOS, and Windows reviewer environments.
- **REJECTED ALTERNATIVE**: Relying on machine-specific global Python environments.
- **COST / RISK**: Environment incompatibility causing immediate gate failure.
- **SOURCE**: Brief p. 2, FAQ Round 1 §2.1, FAQ Round 2 §1.1

---

### D-23: Adoption of Failure Progression & Deterioration Score Engine (Innovation 1)
- **DECISION ID**: D-23
- **QUESTION**: Should temporal deterioration and surge features (recent 7d vs prior 21d baseline) be integrated into the operational pipeline?
- **WHY IT MATTERS**: Pure static snapshots fail to distinguish between chronic benign noise and acute active degradation trajectories.
- **OPTIONS**:
  1. Option A: Current-state static features only (Baseline V1).
  2. Option B: Static features + linear trend regression slopes.
  3. Option C: Static features + normalized delta surges + bounded composite Deterioration Score ($D \in [0.0, 1.0]$).
- **EVIDENCE REQUIRED**: Retrospective 16-week operational cost, Precision@15, and Gateway-Disjoint CV generalization.
- **EXPERIMENT REQUIRED**: Experiments E-D01, E-D02, E-D03, E-D04.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Adopt Option C (Normalized Deltas and Bounded Composite Deterioration Score).
- **REASON**: Deltas quantify acute degradation trajectories while suppressing false alarms from chronically noisy but operational gateways. Bounded $[0.0, 1.0]$ formulation prevents numerical divergence.
- **REJECTED ALTERNATIVE**: Unbounded regression slopes (sensitive to small sample counts and high-variance spikes).
- **COST / RISK**: Minimal complexity addition; guarded against cold-start assets via neutral default.

---

### D-24: Failure Signatures as Diagnostic Explainability & Feature Layer (Innovation 2)
- **DECISION ID**: D-24
- **QUESTION**: How should recognizable operational failure modes (backhaul collapse, watchdog resets, silence blackouts) be represented?
- **WHY IT MATTERS**: Technicians require actionable physical diagnostic explanations to prepare appropriate replacement hardware before truck rolls.
- **OPTIONS**:
  1. Option A: Pure continuous ML probabilities with post-hoc SHAP explanations.
  2. Option B: 5 deterministic, telemetry-grounded operational failure signatures (`SIG_01` to `SIG_05`) generating human-readable diagnostic tags ($\le 300$ chars) and composite signature score.
  3. Option C: Hand-coded rule-based dispatch without ML.
- **EVIDENCE REQUIRED**: Relative risk ratios for next-week collection deficits, prevalence, and explanation fidelity.
- **EXPERIMENT REQUIRED**: Experiment E-S01.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Adopt Option B as both an auxiliary feature and the primary diagnostic explanation engine in `predictions.csv`.
- **REASON**: Signatures exhibit substantial relative risk multiplication and provide field-ready diagnostic context (e.g. "Backhaul Outage Pattern; Power-Cycle Instability") compliant with the $\le 300$ character explanation requirement.
- **REJECTED ALTERNATIVE**: Pure SHAP feature importance lists (confusing to field dispatch teams; computationally expensive).
- **COST / RISK**: Zero lookahead risk; evaluated strictly on pre-decision telemetry ($t < T$).

---

### D-25: Role of Gateway-Specific Historical Baselines (Innovation 3)
- **DECISION ID**: D-25
- **QUESTION**: Should gateways be evaluated against their own 28-day operating distributions rather than global fleet distributions?
- **WHY IT MATTERS**: Fleet heterogeneity (Yagi 9dBi directional vs Omni 3dBi, Pole vs Indoor) creates substantial variation in normal baseline telemetry.
- **OPTIONS**:
  1. Option A: Global fleet thresholds only.
  2. Option B: Gateway self-baselines with strict 72-hour cold-start fallback (Champion C3).
  3. Option C: Unconstrained individual gateway baselines without cold-start safeguards.
- **EVIDENCE REQUIRED**: Performance on unseen gateways in Gateway-Disjoint CV.
- **EXPERIMENT REQUIRED**: Experiment E-G01 and Combination C3.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Adopt Option B (Gateway Self-Baselines with 72h Cold-Start Guard as Core Feature Family).
- **REASON**: Empirical benchmarking demonstrates that Gateway-Specific Baselines provide the single largest operational improvement of the entire Innovation Phase: reduces 16-week operational cost to **€115,200** (-€13,200 vs Baseline V1), cuts unaddressed faults from 62 to **40**, boosts recall to **89.25%**, and drives unseen gateway PR-AUC from 0.6777 to **0.7658** with the lowest fold variance (€1,489) in the fleet.
- **REJECTED ALTERNATIVE**: Option A (global thresholds only miss asset-specific step changes); Option C (unconstrained baselines without cold-start diverge on young assets).
- **COST / RISK**: Requires 28-day pre-decision lookback window; cold-start guard ensures safe default for assets with <72 hours telemetry.

---

### D-26: Decoupling Risk from Deterioration via Dispatch Priority Engine (Innovation 4)
- **DECISION ID**: D-26
- **QUESTION**: Should technician dispatch be driven purely by static failure risk $P(\text{deficit})$, or by a decoupled Priority Engine combining Risk $\times$ Deterioration?
- **WHY IT MATTERS**: Rapidly deteriorating assets with intermediate static risk ($P \approx 0.45, D \approx 0.90$) may be missed by a strict top-15 risk cutoff, collapsing into unaddressed €600/week penalty episodes.
- **OPTIONS**:
  1. Option A: Pure risk ranking ($\text{score} = P$).
  2. Option B: Multiplicative priority interaction ($S = P \times (1 + \beta D)$).
  3. Option C: Additive weighted blend ($S = \alpha P + (1 - \alpha) D$).
  4. Option D: Quadrant Classification Boost (Critical Accelerating + Emerging candidates boosted).
- **EVIDENCE REQUIRED**: Retrospective 16-week operational cost, lead-time detection rate (Weeks -4 to 0), and repeat visit count.
- **EXPERIMENT REQUIRED**: Experiment E-P01.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Retain Priority Engine as a Validated Research Alternative (C10), while keeping Pure Risk Ranking as Champion Dispatch (C3).
- **REASON**: While Borda ranking cut repeat visits from 52 to 50 and Quadrant Boost intercepted faults at Week -1, ranking adjustments altered probability calibration, resulting in €117,600 total cost vs €115,200 for pure C3 risk ranking.
- **REJECTED ALTERNATIVE**: Enforcing priority engine over superior calibrated risk ranking without operational cost advantage.
- **COST / RISK**: Must maintain deterministic tie-breaking (`-priority_score, gateway_id`).

---

### D-27: Evaluation & Boundary of Unsupervised Fleet Novelty Detector (Innovation 5)
- **DECISION ID**: D-27
- **QUESTION**: How should unsupervised anomaly detection (Isolation Forest) be positioned within the operational decision hierarchy?
- **WHY IT MATTERS**: The test evaluation may contain unseen operating regimes, but labeling "novel as faulty" creates severe false-positive dispatch waste.
- **OPTIONS**:
  1. Option A: Novelty as an independent dispatch selector.
  2. Option B: Novelty as an input feature to the supervised risk model.
  3. Option C: Novelty strictly as an auxiliary forensic monitoring / OOD alert layer.
- **EVIDENCE REQUIRED**: Correlation between novelty score and true deficits, overlap breakdown against HGB predictions, and forensic characterization of flagged anomalies.
- **EXPERIMENT REQUIRED**: Experiment E-N01.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Adopt Option C (Auxiliary Telemetry Drift / Data Quality Auditor; rejected from primary dispatch).
- **REASON**: Forensic audit demonstrates that unsupervised novelty primarily flags extreme telemetry missingness and specialized hardware configurations (Yagi 9dBi high-traffic nodes) rather than operational failure. Standalone dispatch increases 16-week cost by +€3,600 (€132,000).
- **REJECTED ALTERNATIVE**: Option A (Novelty-driven dispatch): severely inflates operational costs (€380 wasted visits).
- **COST / RISK**: Preserves ML model focus on collection-critical degradation modes.

---

### D-28: Final Promoted Innovation Candidate Architecture (Combination Synthesis)
- **DECISION ID**: D-28
- **QUESTION**: Which minimal, non-redundant combination of validated innovations should constitute the final submission pipeline?
- **WHY IT MATTERS**: Complexity firewall prohibits adding features that do not demonstrate independent operational value.
- **OPTIONS**:
  1. Option A: Keep Baseline V1 unchanged (€128,400).
  2. Option B: Champion Candidate C3 (Baseline 29 + 3 Gateway-Specific Baseline Features, €115,200).
  3. Option C: Alternative Priority Candidate C10 (Base + Det + Sig + Priority Engine, €117,600).
- **EVIDENCE REQUIRED**: Head-to-head operational cost, Precision@15, Recall, and dual CV generalization across Combinations C0 to C10.
- **EXPERIMENT REQUIRED**: Combinations C0 through C10.
- **CURRENT STATUS**: SETTLED [CANDIDATE DECISION supported by OBSERVED DATA]
- **FINAL DECISION**: Adopt Option B (Candidate C3 as Champion Dispatch Pipeline, with Failure Signatures and Deterioration as Diagnostic Explanation Layer).
- **REASON**: C3 achieves the lowest 16-week operational cost (€115,200), lowest unaddressed faults (40), highest Recall (89.25%), highest unseen-gateway PR-AUC (0.7658), and lowest fold variance (€1,489) without adding unnecessary hyperparameter complexity. Failure Signatures (`SIG_01`–`SIG_05`) supply the required compliant ($\le 300$ chars) diagnostic reason tags.
- **REJECTED ALTERNATIVE**: Option A (fails to capture €13,200 in proven savings); Option C (costs €2,400 more and increases complexity without generalization benefit).
- **COST / RISK**: Fully reproducible, deterministic, and verified against all temporal, spatial, and economic firewalls.


