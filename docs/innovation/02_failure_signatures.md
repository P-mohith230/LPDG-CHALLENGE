# Innovation 2: Failure Signature Engine & Domain Deficit Associations

## Problem Statement
While gradient boosting models output continuous failure probabilities $P(\text{deficit} \mid X) \in [0, 1]$, continuous probabilities provide zero mechanical explanation to operations teams. When a technician is dispatched to a remote pole or rooftop, they require actionable diagnostic context:
- Is the gateway suffering an acute backhaul outage?
- Is it experiencing repeated watchdog/power-cycle hardware resets?
- Is it suffering from RF front-end noise or antenna mismatch?

Without structural diagnostic signatures, technicians cannot prepare appropriate replacement parts (e.g., replacement antenna, power supply, cellular modem, or SIM card), leading to repeated truck rolls or unaddressed failure modes.

## Empirical Hypothesis
Engineering 5 deterministic, telemetry-grounded operational failure signatures:
1. Provides an interpretable, domain-specific diagnostic layer that maps directly to field failure modes.
2. Identifies specific multi-signal failure archetypes that exhibit statistically elevated relative risk ratios for next-week severe collection deficits ($\text{read\_ratio} < 0.50$).
3. Generates human-readable, evidence-based diagnostic tags ($\le 300$ characters) for dispatch explanations in `predictions.csv`.

## Methodology & Signature Formulations
All signature evaluations operate strictly on pre-decision telemetry ($t < T$). Each signature evaluates measurable multi-metric thresholds:

### 1. `SIG_01_CONNECTIVITY_COLLAPSE` (Backhaul Failure)
- **Conditions**:
  - `feat_sum_disconnections` $\ge 10$
  - `feat_offline_hours` $\ge 24.0\text{ hours}$
  - `feat_missing_hours` $\ge 12\text{ hours}$
- **Field Interpretation**: Cellular modem disconnect loop accompanied by extended backhaul unavailability.

### 2. `SIG_02_HARDWARE_POWER_CYCLE_SURGE` (Power & Watchdog Instability)
- **Conditions**:
  - `feat_power_cycle_cnt` $\ge 2$
- **Field Interpretation**: Repeated hardware cold restarts / power-supply drops. Stage 2 and 3 empirical forensics proved power-cycle events are $13.4\times$ elevated in verified physical repair episodes.

### 3. `SIG_03_PERSISTENT_SILENCE_BLACKOUT` (Prolonged Telemetry Blackout)
- **Conditions**:
  - `feat_tail_silence` $\ge 24.0\text{ hours}$ (zero telemetry received in final 24 hours of decision window)
  - `feat_missing_ratio` $\ge 0.50$ (gateway absent for $\ge 50\%$ of weekly reporting hours)
- **Field Interpretation**: Total system silence or terminal outage entering the decision boundary.

### 4. `SIG_04_RADIO_DOWNLINK_DEGRADATION` (RF Front-End / Downlink Path Loss)
- **Conditions**:
  - `feat_mean_rssi_bad` $\ge 2.0$
  - `feat_mean_load1` $\ge 1.5$
  - `feat_tot_tx_success` $< 50$
- **Field Interpretation**: Degraded RF signal quality coupled with processing congestion and collapsing packet delivery.

### 5. `SIG_05_MULTI_DOMAIN_CRISIS` (Compound Multi-System Failure)
- **Conditions**: Simultaneous active breaches across at least 3 distinct telemetry domains:
  - Domain A (Backhaul): Offline $\ge 12\text{h}$ or Disconnections $\ge 10$
  - Domain B (Availability): Missing hours $\ge 24\text{h}$ or Tail silence $\ge 12\text{h}$
  - Domain C (Stability): Power cycles $\ge 2$ or Total reboots $\ge 5$
- **Field Interpretation**: Cascading hardware and network collapse requiring urgent physical intervention.

### Composite Signature Score ($S \in [0.0, 1.0]$)
$$S = \min\left(1.0, 0.25 \cdot \text{SIG}_1 + 0.20 \cdot \text{SIG}_2 + 0.25 \cdot \text{SIG}_3 + 0.10 \cdot \text{SIG}_4 + 0.20 \cdot \text{SIG}_5\right)$$

## Experimental Diagnostics
- **Prevalence**: Percentage of fleet gateway-weeks exhibiting each signature.
- **Target Association**: Incidence of next-week severe collection deficit ($\text{read\_ratio} < 0.50$) when signature is active vs inactive.
- **Relative Risk Ratio ($RR$)**:
  $$RR = \frac{P(\text{deficit} \mid \text{SIG} = 1)}{P(\text{deficit} \mid \text{SIG} = 0)}$$
- **Overlap Analysis**: Fraction of top-15 ML predictions that triggered at least one signature.

## Results & Findings

### Diagnostic Signature Validation Table ($N=6,927$ Gateway-Weeks)

| Signature ID | Telemetry Description | Prevalence (%) | Trigger Count | Deficit Rate (Active) | Deficit Rate (Inactive) | Relative Risk Ratio ($RR$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`SIG_01`** | **Backhaul Connectivity Collapse** | 5.85% | 405 | **71.11%** | 4.03% | **$17.63\times$** |
| **`SIG_02`** | **Hardware Power-Cycle Surge** | 4.03% | 279 | **55.91%** | 5.94% | **$9.41\times$** |
| **`SIG_03`** | **Persistent Silence Blackout** | 12.99% | 900 | **46.22%** | 2.24% | **$20.63\times$** |
| **`SIG_04`** | **Radio Downlink Degradation** | 1.18% | 82 | **69.51%** | 7.22% | **$9.63\times$** |
| **`SIG_05`** | **Multi-Domain Compound Crisis** | 5.66% | 392 | **59.95%** | 4.84% | **$12.40\times$** |

### Machine Learning Feature Inclusion Benchmark
- Baseline 31 Features: **€128,400** (Visit: €91,200, Penalty: €37,200).
- Baseline + `feat_signature_score`: **€130,200** (Visit: €91,200, Penalty: €39,000).
- **Finding**: Adding rule-based signature scores directly into the feature space of HistGradientBoosting slightly degraded operational cost (+€1,800), as the gradient booster already splits on the underlying continuous telemetry features. Forcing boolean combinations created slight sub-optimal leaf splits.

## Interpretation & Operational Insights
1. **Extreme Diagnostic Selectivity**: All 5 signatures demonstrate extraordinary relative risk ratios ($9.41\times$ to $20.63\times$). When `SIG_01` or `SIG_03` triggers, the empirical probability of severe meter collection deficit exceeds $70\%$ and $46\%$ (compared to $<4\%$ for inactive fleet assets).
2. **Actionable Root-Cause Attribution**: Rather than generic failure probabilities, field technicians receive concrete diagnostic tags (e.g., `"Backhaul Outage Pattern; Power-Cycle Instability"`).
3. **Role Decoupling**: Signatures are empirically proven to be an **explanation and post-ranking triage engine**, rather than an internal gradient booster feature.

## Limitations
1. **Rule Discretization**: Hard thresholding introduces edge sensitivity (e.g., 9 disconnections vs 10).
2. **Non-Exhaustiveness**: Non-standard degradation patterns that do not meet the exact multi-domain boolean conditions will not trigger a signature.

## Decision
**PROMOTED AS PRIMARY EXPLAINABILITY ENGINE & DIAGNOSTIC TAG GENERATOR**. Signatures provide the programmatic foundation for field explanations ($\le 300$ chars) in `predictions.csv`, but are excluded from raw gradient boosting inputs to avoid redundant boolean threshold partitioning.
