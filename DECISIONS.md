# LPDG 2026 — Project Decisions

**Project**: LPDG Innovation Hub Selection Challenge 2026  
**Candidate Registration ID**: `23091A3286`  
**Selected Part 2 Specialization**: **Track D — Data Science & Track E — Machine Learning** (Dual Specialization)  

---

## Decision 1 — Target Definition

### Choice:
Forward 1-Week Smart-Meter Collection Deficit:
$$Y_{g, k+1} = \mathbb{I}\left(\frac{\text{meters\_read}_{g, k+1}}{\text{meters\_expected}_{g, k+1}} < 0.50\right)$$
evaluated over $[T, T + 7\text{d})$ where $T = \text{Monday 00:00:00 UTC}$.

### Alternatives Considered:
1. **Binary Zero Reads ($\text{meters\_read} == 0$)**: Only 2 positive instances observed across 6 months (0.03% prevalence), rendering it statistically degenerated and unlearnable.
2. **Field Technician Repair Outcome (`Fehler behoben`)**: Only 114 positive instances (1.65% prevalence). Severely capacity-constrained by historical technician staffing, and 60.7% of historical visits were recorded as `Kein Fehler gefunden` (substantial outcome noise).
3. **Telemetry Silence Alone ($\ge 24\text{h}$ Missing)**: 31.28% prevalence with extreme monthly volatility (9.14% standard deviation), inducing massive false-positive dispatches during routine network provider maintenance.

### Why:
Smart meter collection collapse directly drives utility financial penalties (€600/week unaddressed fault). Target A1 exhibits a stable 7.95% fleet prevalence (551 positive pairs across 106 unique gateways), low monthly variance (0.90% standard deviation), and 99.5% co-occurrence with physical backhaul/power outages, providing an operationally grounded learning target.

### Trade-off:
Meter collection records terminate on `2026-01-26`. The model must therefore infer future collection risk during the February–March 2026 evaluation period purely from pre-decision telemetry signatures without receiving live meter collection feedback.

---

## Decision 2 — Feature Engineering

### Choice:
Leakage-Safe 32-Feature Matrix combining:
- **29 Audited Baseline Features**: Distinct hourly availability, wall-clock bounded peak event offline duration ($\le 168.0\text{h}$), power-cycle bursts, cellular RSSI/transmit success, and German site category mappings.
- **3 Gateway-Specific Historical Baseline Features**: 28-day self-reference z-scores and relative anomaly scoring with a strict 72-hour cold-start fallback.

### Alternatives Considered:
1. **All 57 Raw Telemetry Columns**: Included 7 zero-variance roaming operator columns, monotonic counter assumptions, and CRC error ratio saturated at 1.0000 ($r = -0.0335$ with collection deficits; rejected as uninformative noise).
2. **Naive Summation of `offline_duration_sec`**: Naively summing the register multiplied frozen event snapshots, producing impossible values (up to 3,901.5 hours in a 168-hour week).
3. **Global Fleet Thresholds Only**: Confounded by static antenna gains (Yagi 9dBi averages 389k packets/week vs 4.6k for Omni 3dBi) and differing meter densities.

### Why:
Gateway self-baselines isolate asset-specific degradation from chronic site noise. In empirical benchmarking, this feature family delivered the single largest operational saving of the Innovation Phase: reducing 16-week operational cost by **€13,200** (from €128,400 to **€115,200**), cutting unaddressed faults from 62 to **40**, and driving spatial Gateway-Disjoint CV PR-AUC from 0.6777 to **0.7658** (+0.0881 improvement on unseen gateways) with the lowest fold standard deviation (€1,489) in the fleet.

### Trade-off:
Requires up to 28 days of historical pre-decision telemetry. Gateways with $<72\text{h}$ of operating history safely fall back to fleet medians (4.30% cold-start prevalence).

---

## Decision 3 — Model Selection

### Choice:
`HistGradientBoostingClassifier` with balanced class weights, learning rate 0.05, max depth 4, and deterministic seed 42.

### Alternatives Considered:
1. **L2-Regularized Logistic Regression**: Failed to capture non-linear interactions between telemetry silence and power-cycle clusters, yielding higher temporal cost (€152,700 vs €144,900) and lower PR-AUC (0.7719 vs 0.7759).
2. **Random Forest**: Achieved comparable PR-AUC (0.7842) but higher operational cost (€152,100) due to uncalibrated probability tails and substantial memory overhead.
3. **Deep Tabular Networks (TabNet / MLP)**: Excessive training latency and parameter fragility, making live code modification during a 35-minute evaluation panel interview high-risk.

### Why:
HistGradientBoosting natively handles missing values, trains in $<2$ seconds on standard hardware, achieves the lowest temporal walk-forward cost (€144,900) and lowest gateway-disjoint cost (€727,500), and outputs well-calibrated continuous probabilities that directly optimize the asymmetric €380 vs €600 cost matrix.

### Trade-off:
Tree-based partition boundaries can introduce discrete probability jumps near decision thresholds rather than smooth gradients.

---

## Decision 4 — Dispatch Policy

### Choice:
2-Week Post-Visit Cooldown Policy with deterministic lexicographical ranking (`-risk_score, gateway_id`).

### Alternatives Considered:
1. **Pure ML Ranking (Zero Cooldown)**: Repeatedly dispatched to the same persistent failing gateways week after week, burning 125 repeat visits and performing worse than the unsupervised 3-Sigma baseline (€172,200 vs €164,400).
2. **1-Week Cooldown**: Insufficient to prevent duplicate dispatches during active repair cycles, incurring 87 repeat visits and €139,800 operational cost.
3. **3-Week Cooldown**: Over-suppressed gateways experiencing genuine secondary failure episodes, slightly increasing operational cost to €129,000.
4. **Heuristic Priority Engine (Rank Borda / Quadrant Boost)**: Cut repeat visits to 50 and intercepted emerging faults at Week -1, but altered calibrated probability ordering, incurring €2,400 higher penalty costs than pure C3 risk ranking (€117,600 vs €115,200).

### Why:
A 2-week cooldown aligns with the physical reality of utility dispatch operations, allowing technician repairs and hardware stabilization. It eliminates 73 redundant visits, maximizes fleet recall at **89.25%**, and achieves the minimum 16-week operational cost of **€115,200**.

### Trade-off:
If an asset suffers a completely independent secondary failure within 14 days of an on-site visit, the cooldown policy delays intervention until the window expires.

---

## Decision 5 — Part 2 Specialization Area

### Choice:
**Track D — Data Science & Track E — Machine Learning** (Integrated Dual Specialization).

### Alternatives Considered:
- **Track A (Data Engineering)**: Batch/stream ingestion and partition management pipelines.
- **Track B (Software Development)**: Standalone microservice scaffolding and REST endpoints.
- **Track C (DevOps)**: Container orchestration, Docker compose setups, and cloud CI/CD runners.
- **Track F (MLOps)**: Centralized model registries, shadow deployments, and dynamic rollbacks.

### Why:
Predictive grid maintenance requires both algorithmic outperformance and operational decision clarity:
1. **Track E (Machine Learning Algorithmic Rigor)**:
   - Slashes 16-week historical proxy benchmark cost from €164,400 to **€115,200** (a **€49,200 / 29.9% cost reduction**) and cuts unaddressed fault penalties from €73,200 to **€24,000** (a **67.2% reduction**).
   - Audited 32 features (29 baseline + 3 gateway self-baselines) with rigorous ablation proving the necessity of self-history z-scores, while pruning saturated CRC error metrics ($R = 1.0000$).
   - Dual adversarial validation: quarterly temporal drift (PR-AUC 0.8465) and device-disjoint spatial validation on unseen hardware (PR-AUC 0.7658).
2. **Track D (Data Science Operational Rigor)**:
   - **Mathematical Operationalization of Dispatch Thresholds**: Modeled the €380 visit cost vs €600 penalty trade-off, showing why fixed probability thresholds fail under storm conditions and implementing an interactive What-If sensitivity tool (*"Move your threshold, and calculate the exact financial cost in each direction"*).
   - **Hardware Cohort Uncertainty Quantification**: Stratified risk across antenna gain types (`Yagi 9 dBi`, `Omni 3 dBi`, `Omni 5 dBi`, `Panel 7 dBi`), meter density tiers, and missingness regimes.
   - **Diagnostic Failure Signatures & Maintenance Playbook**: Formalized 5 domain failure signatures (`SIG_01`–`SIG_05`) and built a concrete technician remediation action playbook.
   - **Interactive Operations Control Center**: Delivered an industrial-grade Streamlit + Three.js decision-support platform with real-time 3D telemetry pillars, Executive Fleet Readiness Matrix, and 8-week multi-visit schedule timelines.

### Trade-off:
Delivering an integrated Data Science + Machine Learning platform meant focusing engineering on decision modeling and interactive operational analytics rather than external web service microservices (Track B) or container clusters (Track C).

---

## Limitations: What the Solution Cannot Do

### 1. Sub-Weekly Micro-Outage Resolution
The pipeline aggregates telemetry into trailing 7-day windows aligned with weekly Monday dispatch boundaries. It cannot detect transient mid-week micro-outages that fully resolve before Sunday 23:59:59 UTC. If a gateway drops offline for 6 hours on Wednesday and recovers, it may receive a low weekly risk score.

### 2. Static Cooldown Duration
The 2-week cooldown is applied uniformly across all assets, regardless of repair complexity. An asset requiring only a simple external antenna realignment is suppressed for the same 14-day duration as an asset undergoing a complete cellular modem replacement.

### 3. Proxy-Target Disconnect
The model predicts smart meter collection collapse ($\text{read\_ratio} < 0.50$), which is an operational proxy rather than direct physical hardware ground truth. Environmental cellular carrier cell tower maintenance or local power outages can trigger collection deficits without internal gateway hardware defects.

### What Another Two Weeks of Development Would Deliver:
1. **Dynamic Signature-Based Cooldown**: Adjust cooldown duration dynamically based on the diagnosed failure signature (e.g. 1 week for radio downlink fade, 3 weeks for full gateway replacement).
2. **Parametric Survival Analysis (Hazard Curves)**: Replace weekly binary classification with continuous survival analysis (Cox Proportional Hazards / Weibull) to estimate Remaining Useful Life (RUL) in hours.
3. **Semi-Supervised Positive-Unlabeled (PU) Calibration**: Apply PU learning algorithms to calibrate unvisited gateways with missing meter collection records, refining out-of-sample probability bounds.
