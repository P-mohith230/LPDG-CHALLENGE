# Innovation 3: Gateway-Specific Historical Baseline & Cold-Start Behavior

## Problem Statement
The LPDG gateway fleet exhibits extreme physical and environmental heterogeneity:
- **Antenna Profiles**: Omni 3dBi (short-range urban) vs Yagi 9dBi directional (high-gain long-range, handling 85x higher packet traffic).
- **Mounting Locations**: Indoor, Outdoor, Pole, Rooftop.
- **Meter Density**: Installations range from 12 meters to > 2,000 meters per gateway.

Under a global fleet-wide baseline, a rooftop gateway in a noisy RF environment that routinely logs 8 disconnections per week looks "abnormal" compared to the fleet average, triggering false-positive alerts. Conversely, an indoor gateway that has operated flawlessly with 0 disconnections for 6 months might suddenly log 6 disconnections—a critical local failure—yet remain below the global 3-sigma fleet threshold.

## Empirical Hypothesis
Computing asset-specific historical baselines from pre-decision telemetry $[T - 28\text{d}, T - 7\text{d})$ and evaluating recent 7-day deviations as normalized Z-scores:
1. Filters out benign site-specific environmental noise.
2. Detects localized anomalies in quiet gateways before full outage occurs.
3. Requires an explicit **Cold-Start Guard** to maintain stability for newly commissioned gateways.

## Methodology & Temporal Firewall
All historical baselines are calculated strictly on data observed prior to the current evaluation week:
$$\text{History Window: } [T - 28\text{d}, T - 7\text{d})$$
$$\text{Recent Window: } [T - 7\text{d}, T)$$
Upper boundary: Strictly $t < \text{Monday 00:00:00 UTC}$. Zero lookahead.

### Cold-Start Guard & Minimum History Logic
- If a gateway has fewer than **72 hours** of historical telemetry in $[T - 28\text{d}, T - 7\text{d})$:
  - Flag `feat_gw_has_adequate_history = 0`.
  - Fallback: Use fleet-wide global mean ($\mu_{\text{fleet}}$) and standard deviation ($\sigma_{\text{fleet}}$) for normalization.
- If a gateway has $\ge 72$ hours of history:
  - Flag `feat_gw_has_adequate_history = 1`.
  - Compute asset-specific mean ($\mu_{\text{gw}}$) and sample standard deviation ($\sigma_{\text{gw}}$).

### Standardized Deviation Metrics
For metric $x \in \{\text{offline\_sec}, \text{disconnections}, \text{reboots}, \text{missing\_hours}\}$:
$$Z_x = \frac{x_{\text{recent}} - \mu_x}{\sigma_x + \epsilon}$$
where $\epsilon = 1.0$ prevents division by zero for zero-variance histories.

### Composite Gateway-Relative Anomaly Score ($A_{\text{gw}} \in [0.0, 1.0]$)
To aggregate multiple independent deviations while punishing positive breaches above normal behavior:
$$\text{pos\_deviations} = \max(0, Z_{\text{offline}}) + \max(0, Z_{\text{disconns}}) + \max(0, Z_{\text{reboots}}) + \max(0, Z_{\text{missing}})$$
$$A_{\text{gw}} = \frac{1}{1 + \exp\left(-1.5 \cdot (\text{pos\_deviations} - 2.0)\right)}$$

## Experimental Plan (E-G01)
1. **Cold-Start Quantification**: Measure prevalence of cold-start gateway-weeks across the 25 decision boundaries.
2. **Economic Benchmarking**: Compare Baseline 31 features vs Baseline + Gateway-Relative features on the unified 16-week window.
3. **Generalization Firewall**: Test whether asset-specific baselines improve or degrade spatial Gateway-Disjoint CV performance.

## Results & Findings

### Cold-Start Analysis
- **Prevalence**: Exactly **4.30%** of fleet gateway-weeks ($N=298$ records) had $< 72\text{ hours}$ of historical telemetry and were seamlessly redirected to the global fleet baseline.
- **Stability**: Zero runtime division-by-zero errors or infinite Z-score anomalies were observed across all 25 decision boundaries.

### Economic & Cross-Validation Benchmark (E-G01 & Combination C3)

| Metric | Baseline V1 (Global) | Baseline + Gateway Baseline (C3) | Absolute Delta | Relative Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **16-Week Total Operational Cost** | **€128,400** | **€115,200** | **-€13,200** | **-10.28% Cost Reduction** |
| Technician Visit Cost (€380/visit) | €91,200 | €91,200 | €0 | Fixed budget (240 visits) |
| Missed Fault Penalty (€600/wk) | €37,200 | €24,000 | -€13,200 | -35.48% Penalty Reduction |
| **Precision@15** | 30.83% | **32.92%** | +2.09% | Higher dispatch yield |
| **Recall on True Fault-Weeks** | 83.33% | **89.25%** | **+5.92%** | Substantial fault capture |
| Intercepted Fault Episodes | 310 | **332** | +22 episodes | Earlier interception |
| Unaddressed Fault Episodes | 62 | **40** | **-22 episodes** | Drastic penalty avoidance |
| Repeat Visits (2-Wk Cooldown) | 52 | 53 | +1 | Controlled policy behavior |
| Wasted Visits | 166 | 161 | -5 | Reduced technician waste |
| **Temporal CV PR-AUC** | 0.7759 | **0.8465** | **+0.0706** | Higher temporal precision |
| **Gateway-Disjoint CV PR-AUC** | 0.6777 | **0.7658** | **+0.0881** | Major generalization gain |
| **Gateway-Disjoint Total Cost** | €727,500 | **€720,900** | **-€6,600** | Robust on unseen assets |

## Interpretation & Operational Insights
1. **Dramatic Deficit Suppression**: Gateway-specific historical baselines produced the single largest independent economic improvement in the entire innovation program, driving retrospective operational costs down to **€115,200** (-€13,200) and reducing unaddressed fault episodes from 62 to 40.
2. **Heterogeneity Compensation**: Evaluating an asset against its own typical behavior prevents false alarms on high-noise rooftop antennas while immediately flagging sudden shifts on quiet indoor meters.
3. **Generalization Evidence**: On completely unseen gateways in Gateway-Disjoint 5-Fold CV, PR-AUC increased from 0.6777 to **0.7658**, providing strong evidence that asset-relative normalization captures generalizable degradation dynamics rather than memorizing gateway IDs.

## Limitations
1. **Non-Stationary Regimes**: If firmware is updated fleet-wide, historical baseline distributions shift, causing temporary artificial elevation in Z-scores until the 28-day window rolls forward.
2. **Persistent Failures**: A gateway failing for $> 3$ weeks will gradually incorporate failure telemetry into its own baseline, lowering its future Z-scores (baseline drift).

## Decision
**PROMOTED AS CHAMPION FEATURE FAMILY (C3)**. Gateway-specific historical baselines with 72h cold-start guards deliver dramatic, verified economic savings (-€13,200), elevate Recall to 89.25%, and exhibit outstanding spatial generalization on unseen gateways.
