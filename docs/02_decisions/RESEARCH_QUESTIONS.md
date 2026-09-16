# Prioritized Project Research Questions
**LPDG Innovation Hub Selection Challenge 2026**  
*Structured Registry of Empirical Investigation Hypotheses & Open Questions*

---

## Purpose & Protocol
In adherence to the LPDG Challenge Brief, Round 1 FAQ, and Round 2 FAQ (specifically Section 8), this document registers all research questions that require empirical resolution through our data analysis and experiment backlog. 

**STRICT COMPLIANCE RULE**: No research question in this document is answered a priori. Every question remains in status `OPEN — REQUIRES INVESTIGATION` until experimental evidence is produced and cross-verified.

---

## Priority Classification Framework
- **CRITICAL**: Foundational operational and architectural choices that directly determine model target formulation, temporal leakage compliance, or the objective function.
- **HIGH**: Load-bearing feature engineering, missing data treatment, threshold economics, and validation split integrity.
- **MEDIUM**: Secondary signal extraction, sensor noise filtering, and model family comparisons.
- **LOW**: Exploratory enhancements, fine hyperparameter tuning, and advanced diagnostic extensions.

---

## CRITICAL Priority Questions

### RQ-01: Operational Definition of "Needs a Visit"
- **Question**: What exact quantitative criteria in historical telemetry correspond to a gateway that genuinely requires an on-site technician dispatch?
- **Why It Matters**: Section 5.1 of Round 2 FAQ explicitly defines this as the primary test of Data Science Judgement (25% weight). The challenge brief does not supply an answer key.
- **Hypotheses Under Consideration**:
  - H1: A gateway "needs a visit" when LoRa meter-read delivery completely ceases ($0\%$ read success) for $\ge 7$ consecutive days.
  - H2: A gateway "needs a visit" when backhaul/cellular silence exceeds 48 hours and fails to self-recover.
  - H3: A gateway "needs a visit" when a composite hardware/radio failure score breaches a calibrated economic cost threshold.
- **Required Evidence**: Cross-tabulation of pre-visit telemetry patterns against confirmed repair records (`Fehler behoben`) in `field_visits.csv` and zero-read weeks in `meter_read_success.csv`.
- **Linked Experiment**: Experiment E-04
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-02: Telemetry Silence — Hardware Failure vs. Observability Artifact
- **Question**: For an active gateway with prolonged telemetry silence (omitted hourly rows in Parquet), is silence a strong indicator of physical hardware/power failure, or does it represent benign network hibernation / telemetry pipeline packet drop?
- **Why It Matters**: Round 2 FAQ §3.4, §8, and our submitted Question 2 leave this intentionally unanswered. Naively treating silence as failure causes false alarm dispatches; ignoring silence misses catastrophic outages.
- **Hypotheses Under Consideration**:
  - H1: Complete silence $\ge 48$ hours strongly predicts subsequent zero meter-reads and confirmed technician dispatches.
  - H2: Short silence (< 12 hours) is pervasive background noise caused by cellular backhaul dropouts and does not correlate with meter collection loss.
- **Required Evidence**: Complete time-grid reindexing; survival curves of silent gateways; correlation between silence duration and meter read failure rate.
- **Linked Experiment**: Experiment E-01 & E-07
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-03: Temporal Target Construction Without Leakage
- **Question**: How can a supervised learning label be constructed from post-cutoff historical telemetry during the training period without leaking information across weekly decision boundaries?
- **Why It Matters**: FAQ Round 2 §4.5 confirms that future historical telemetry may be used to engineer labels, provided cutoff rules are respected. Any target leakage invalidates model evaluation.
- **Hypotheses Under Consideration**:
  - H1: Binary indicator $Y_{g, k} \in \{0, 1\}$ defined as whether gateway $g$ suffers active fault status during week $k+1$ using strictly $[T, T+7\text{d})$ telemetry for labels and $[T-28\text{d}, T)$ for features.
  - H2: Continuous surrogate target tracking weekly meter-read deficit or unaddressed outage hours.
- **Required Evidence**: Class balance, temporal stationarity, and zero correlation between feature noise and future label generation.
- **Linked Experiment**: Experiment E-04 & E-08
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-04: Economic Thresholding & The €380 vs. €600 Asymmetry
- **Question**: At what predicted failure probability or risk score does the expected savings from preventing a €600/week unaddressed fault exceed the certain €380 visit cost under a hard 15-visit weekly constraint?
- **Why It Matters**: Standard ML loss functions optimize symmetric metrics (accuracy, log-loss) or balanced trade-offs (F1). Operational evaluation depends strictly on asymmetric cash flow (FAQ Round 2 §4.2).
- **Hypotheses Under Consideration**:
  - H1: Pure cost-based ranking $\text{Score}_g = P(\text{fault}_g) \times €600 - €380$ provides optimal weekly prioritization.
  - H2: Rank ordering must incorporate anticipated episode duration (preventing multi-week compounding losses).
- **Required Evidence**: Empirical evaluation of simulated operational cost curves across threshold sweeps.
- **Linked Experiment**: Experiment E-09
- **Status**: `OPEN — REQUIRES INVESTIGATION`

---

## HIGH Priority Questions

### RQ-05: Operational Cooldown & Repeat Selection Suppression
- **Question**: How many weeks of operational cooldown must be enforced on a visited gateway to prevent burning €380 visits on the same ongoing fault episode?
- **Why It Matters**: FAQ Round 2 §4.1 confirms that repeat visits during the same fault episode provide €0 cost reduction, waste €380, and consume 1 of the 15 scarce weekly slots.
- **Hypotheses Under Consideration**:
  - H1: A fixed 2-week lockout window maximizes cost efficiency.
  - H2: Dynamic cooldown that allows re-selection only if telemetry indicates a return to healthy operation followed by a new distinct failure signature.
- **Required Evidence**: Historical work order repeat visit intervals in `field_visits.csv` and synthetic episode simulation.
- **Linked Experiment**: Experiment E-10
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-06: Missing-Data Handling & Ranking Sensitivity
- **Question**: How sensitive are gateway anomaly scores and top-15 rankings to the mathematical representation of missing hourly records (omitted rows vs. zero imputation vs. rate normalization)?
- **Why It Matters**: FAQ Round 2 §3.3 highlights that missing data substantially alters ranking outcomes and demands an explicit sensitivity study.
- **Hypotheses Under Consideration**:
  - H1: Normalizing counts by active reporting hours prevents unfair penalization of newly commissioned or temporarily intermittent gateways.
  - H2: Explicitly separating "unreported hours" as an independent feature out-performs both zero-filling and row-dropping.
- **Required Evidence**: Rank correlation (Spearman's $\rho$, Jaccard@15 overlap) between ranking models with alternative missing data strategies.
- **Linked Experiment**: Experiment E-02
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-07: Offline Duration & Meter-Read Success Relationship
- **Question**: What is the quantitative empirical transfer function between cellular backhaul offline duration (`offline_duration_sec`) and smart meter read success rate?
- **Why It Matters**: Directly posed by LPDG in FAQ Round 2 Section 8. Backhaul outages do not necessarily cause meter data loss if gateway local buffers persist.
- **Hypotheses Under Consideration**:
  - H1: Short cellular outages (< 6 hours) have zero impact on weekly meter reads due to on-device LoRa message buffering.
  - H2: Outages exceeding 24 hours cause buffer overflow and a steep non-linear drop in meter-read success.
- **Required Evidence**: Scatter plots, piecewise linear regression, and mutual information between weekly summed offline seconds and `meters_read / meters_expected`.
- **Linked Experiment**: Experiment E-03
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-08: Reboot Frequency & Hardware Failure Attribution
- **Question**: Does elevated reboot frequency (`reboot_cnt`) reliably identify gateways that require physical hardware intervention, or does it reflect benign watchdog resets?
- **Why It Matters**: Frequently posed by LPDG in Section 8. `field_visits.csv` shows 110 dispatches for `Haeufige Neustarts`, yet 60.7% of all visits found no fault.
- **Hypotheses Under Consideration**:
  - H1: Power-cycle reboots (`r_cnt_power_cycle`) strongly correlate with hardware power supply degradation (`Netzteil` replacements).
  - H2: Software reboots (`r_cnt_reboot`) without power cycle are predominantly benign self-healing watchdog actions.
- **Required Evidence**: Breakdown of reboot causes vs. technician outcomes (`Fehler behoben` with parts replaced).
- **Linked Experiment**: Experiment E-04
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-09: Gateway-Disjoint vs. Forward-Time Generalization
- **Question**: What is the quantitative generalization gap when evaluating anomaly models on (a) unseen gateways in known weeks versus (b) seen gateways in future weeks versus (c) unseen gateways in future weeks?
- **Why It Matters**: FAQ Round 2 §5.2 and §6.9 mandate validation on both dimensions and reporting performance spreads rather than point estimates.
- **Hypotheses Under Consideration**:
  - H1: Random splitting severely overestimates model performance due to gateway identity memorization.
  - H2: Grouped gateway splits with forward-chaining time folds provide an honest estimate of live deployment cost.
- **Required Evidence**: Cross-validation cost variance and metric range across 5 grouped temporal folds.
- **Linked Experiment**: Experiment E-12, E-13, E-14
- **Status**: `OPEN — REQUIRES INVESTIGATION`

---

## MEDIUM Priority Questions

### RQ-10: Recent vs. Historical Window Weighting
- **Question**: What relative weighting between immediate short-term signals ($T-24\text{h}$, $T-7\text{d}$) and long-term operating baselines ($T-28\text{d}$) yields optimal early detection without excessive noise?
- **Why It Matters**: FAQ Round 2 §3.5 discusses the trade-off between fast volatile signals and delayed stable signals.
- **Hypotheses Under Consideration**:
  - H1: Velocity and acceleration features ($\Delta \text{metric}_{7\text{d}} - \Delta \text{metric}_{28\text{d}}$) predict acute degradation better than static levels.
- **Linked Experiment**: Experiment E-06
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-11: RF Noise Discrimination (CRC Corruptions vs. True Loss)
- **Question**: Since over 99% of RF packets fail CRC across the entire fleet, how can genuine LoRa RF receiver degradation be separated from ambient ISM band noise?
- **Hypotheses Under Consideration**:
  - H1: Ratios of good packets to expected meters (`rx_nr_pkts / n_meters_installed`) provide a normalized RF health index.
  - H2: Sudden drops in received packets without an increase in RSSI/SNR indicate local RF front-end failure.
- **Linked Experiment**: Experiment E-05
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-12: Supervised ML vs. Cost-Calibrated Anomaly Ranking
- **Question**: Does a supervised gradient-boosted decision tree (LightGBM/CatBoost) trained on synthetic proxy labels reliably beat a disciplined, cost-calibrated statistical baseline on operational cost?
- **Why It Matters**: FAQ Round 2 §4.2 emphasizes that higher complexity without cost reduction is penalized under Judgement.
- **Hypotheses Under Consideration**:
  - H1: Supervised models capture multi-signal interactions (e.g. memory leak + reboot frequency) that 3-sigma thresholds miss.
  - H2: Simpler robust rankers with operational cooldown may outperform complex models prone to distribution shift.
- **Linked Experiment**: Experiment E-11
- **Status**: `OPEN — REQUIRES INVESTIGATION`

---

## LOW Priority Questions

### RQ-13: Cellular Operator & Roaming Performance Disparities
- **Question**: Do failure and disconnection rates differ systematically across cellular operators (`TelekomDE`, `VodafoneDE`, `O2DE`), and should operator-specific baselines be applied?
- **Status**: `OPEN — REQUIRES INVESTIGATION`

### RQ-14: Environmental & Site Type Robustness
- **Question**: Do gateways located in boiler rooms (`Heizraum`) or outdoor masts (`Außenmast`) exhibit different thermal/reboot dynamics requiring stratified anomaly thresholds?
- **Status**: `OPEN — REQUIRES INVESTIGATION`

---

## Traceability & Status Summary

| RQ ID | Priority | Linked Experiment | Required Evidence Source | Current Status |
|---|---|---|---|---|
| **RQ-01** | CRITICAL | E-04 | `field_visits.csv`, `meter_read_success.csv`, telemetry | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-02** | CRITICAL | E-01, E-07 | Telemetry time-grid reindexing, survival analysis | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-03** | CRITICAL | E-04, E-08 | Post-cutoff telemetry, leakage assertions | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-04** | CRITICAL | E-09 | Cost simulation curve, threshold sweep | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-05** | HIGH | E-10 | Work order revisit history, episode simulation | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-06** | HIGH | E-02 | Missing data sensitivity runs, Spearman $\rho$ | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-07** | HIGH | E-03 | Telemetry vs. meter read success regression | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-08** | HIGH | E-04 | Reboot attribution vs. technician repair logs | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-09** | HIGH | E-12, E-13, E-14 | Grouped k-fold, temporal fold variance | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-10** | MEDIUM | E-06 | Multi-resolution window evaluation | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-11** | MEDIUM | E-05 | RF packet ratios, CRC corruption analysis | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-12** | MEDIUM | E-11 | Baseline vs. ML cost comparison harness | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-13** | LOW | E-05 | Operator cross-tabulation | `OPEN — REQUIRES INVESTIGATION` |
| **RQ-14** | LOW | E-05 | Site type stratification | `OPEN — REQUIRES INVESTIGATION` |
