# Innovation 1: Failure Progression & Deterioration Score Engine

## Problem Statement
The Stage 1–9 baseline architecture (`BASELINE_V1`) evaluates gateways based strictly on static 7-day telemetry snapshots in the window $[T - 7\text{d}, T)$. While static features accurately identify gateways that are already in a state of severe failure (e.g., total silence for 7 days), they cannot distinguish between:
1. **Chronic Stable Noise**: A gateway that persistently logs 10 disconnections and 12 offline hours every week due to local cellular topology, but reliably delivers its meter reads.
2. **Acute Progressive Deterioration**: A gateway that historically operated with 0 disconnections and 0 offline hours, but suddenly surges to 10 disconnections and 12 offline hours in the trailing week.

Under a pure static model, both gateways produce identical risk features. However, the rapidly deteriorating gateway is on an active failure trajectory toward an unaddressed fault episode, incurring €600/week in SLA penalties if not intercepted early.

## Empirical Hypothesis
Quantifying the first-order temporal difference ($\Delta$) and normalized surge ratios between the trailing 7-day observation window $[T - 7\text{d}, T)$ and the preceding 21-day historical baseline $[T - 28\text{d}, T - 7\text{d})$ provides independent early-warning signals that:
1. Increase Precision@15 and Recall on developing operational deficits before full blackout.
2. Reduce retrospective operational costs below the €128,400 benchmark.
3. Generalize stably across forward time folds and unseen gateways.

## Methodology & Temporal Firewall
All metrics are computed strictly using telemetry timestamped prior to Monday 00:00:00 UTC ($t < T$). Zero future telemetry, visit records, or meter-read data are accessed.

### Window Definitions
- **Recent Window ($W_{\text{recent}}$)**: $[T - 7\text{d}, T)$ (168 hours).
- **Prior Reference Window ($W_{\text{prior}}$)**: $[T - 28\text{d}, T - 7\text{d})$ (504 hours, normalized to a 168-hour equivalent by dividing cumulative sums by 3.0).

### Engineered Deterioration Signals
1. **Absolute Trajectory Deltas**:
   $$\Delta_{\text{offline}} = \text{offline\_hours}_{\text{recent}} - \frac{\text{offline\_hours}_{\text{prior}}}{3.0}$$
   $$\Delta_{\text{missing}} = \text{missing\_hours}_{\text{recent}} - \frac{\text{missing\_hours}_{\text{prior}}}{3.0}$$
   $$\Delta_{\text{disconns}} = \text{disconns}_{\text{recent}} - \frac{\text{disconns}_{\text{prior}}}{3.0}$$
   $$\Delta_{\text{reboots}} = \text{reboots}_{\text{recent}} - \frac{\text{reboots}_{\text{prior}}}{3.0}$$
   $$\Delta_{\text{power\_cycles}} = \text{power\_cycles}_{\text{recent}} - \frac{\text{power\_cycles}_{\text{prior}}}{3.0}$$

2. **Normalized Surge Ratios**:
   $$\text{surge}_x = \frac{\max(0, x_{\text{recent}} - x_{\text{prior\_norm}})}{x_{\text{prior\_norm}} + 1.0}$$
   Evaluated for missing hours, offline hours, and reboot counts.

3. **Bounded Composite Deterioration Score ($D \in [0.0, 1.0]$)**:
   A non-linear bounded score combining standardized surge rates and transition severity:
   $$D = \min\left(1.0, 0.35 \cdot \text{surge}_{\text{missing}} + 0.35 \cdot \text{surge}_{\text{offline}} + 0.15 \cdot \text{surge}_{\text{reboot}} + 0.15 \cdot I(\Delta_{\text{power\_cycles}} > 0)\right)$$

## Experimental Matrix
- **E-D01**: Baseline 31 current-state features only.
- **E-D02**: Baseline + simple absolute deltas ($\Delta_{\text{missing}}$, $\Delta_{\text{offline}}$, $\Delta_{\text{disconns}}$, $\Delta_{\text{reboots}}$, $\Delta_{\text{power\_cycles}}$).
- **E-D03**: Baseline + deltas + normalized surge ratios.
- **E-D04**: Baseline + composite Deterioration Score ($D$).

## Evaluation Protocols
1. **Unified 16-Week Economic Benchmark Window**: `2025-10-06` to `2026-01-19`, exactly 240 technician dispatches (€380/visit, €600 unaddressed fault penalty/week, 2-week cooldown).
2. **Temporal Walk-Forward CV**: Expanding chronological windows.
3. **Gateway-Disjoint CV**: Spatial 5-fold cross-validation on unseen gateway IDs.

## Results & Findings

### Quantitative Performance Comparison

| Experiment ID | Feature Architecture | 16-Wk Total Cost (€) | Penalty Cost (€) | Precision@15 | Recall | Intercepted Faults | Unaddressed Faults | Temporal PR-AUC | Gateway-Disjoint PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **E-D01** | Baseline 31 Features (Frozen Reference) | €128,400 | €37,200 | 30.83% | 83.33% | 310 | 62 | 0.7759 | 0.6777 |
| **E-D02** | Baseline + Absolute Deltas (34 cols) | €121,800 | €30,600 | 31.67% | 86.29% | 321 | 51 | 0.8078 | 0.7538 |
| **E-D03** | Baseline + Deltas + Surge Ratios (37 cols) | **€120,000** | **€28,800** | **31.67%** | **87.10%** | **324** | **48** | **0.8082** | **0.7544** |
| **E-D04** | Baseline + Composite Det Score (30 cols) | €121,200 | €30,000 | 30.83% | 86.56% | 322 | 50 | 0.8271 | 0.7416 |

### Cross-Validation & Generalization Stability
1. **Temporal Walk-Forward CV**:
   - E-D01: Total Cost €144,900 (Mean: €48,300, Std: €7,229, PR-AUC: 0.7759).
   - E-D03: Total Cost **€128,700** (Mean: €42,900, Std: €2,888, PR-AUC: **0.8082**).
   - **Improvement**: Cost reduction of **€16,200** (-11.2%) with fold variance reduced by **60%** (std dropped from €7,229 to €2,888).
2. **Spatial Gateway-Disjoint CV (Unseen Gateways)**:
   - E-D01: Total Cost €727,500 (PR-AUC: 0.6777).
   - E-D03: Total Cost **€720,900** (PR-AUC: **0.7544**).
   - **Improvement**: Cost reduction of **€6,600** on unseen gateways with a massive **+0.0767 PR-AUC** generalization gain.

## Interpretation & Operational Insights
1. **Deltas Capture True Physical Progression**: Adding trend deltas and surge ratios suppresses penalty costs from €37,200 down to €28,800 (-€8,400), intercepting 14 additional severe deficit episodes before collection buffers overflow.
2. **False-Positive Suppression**: Gateways with chronic high disconnection counts but stable historical baselines ($\Delta \approx 0$) are deprioritized, preventing wasted technician dispatches.
3. **Statistical Orthogonality**: Pearson correlation between baseline `feat_offline_hours` and `feat_det_offline_hours_delta` is only **+0.1535** (2.3% shared variance), confirming that deterioration adds genuinely new information rather than duplicating static 7-day features.

## Limitations
1. **Cold-Start Vulnerability**: New gateways with $< 7$ days of prior history cannot compute a 21-day prior baseline; for these assets, the deterioration delta defaults to 0.0 (neutral).
2. **Seasonal Fleet Shifts**: Network-wide weather or backhaul outages can artificially inflate fleet-wide deterioration deltas simultaneously.

## Decision
**PROMOTED TO FINAL ARCHITECTURE**. Trend deltas and the composite Deterioration Score produce verified operational cost reductions across all evaluation protocols (€128,400 $\to$ €120,000) and stabilize out-of-sample generalization on unseen gateways.
