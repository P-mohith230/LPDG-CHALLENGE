# Innovation 5: Unsupervised Fleet Novelty & Out-of-Distribution Detector

## Problem Statement
Supervised machine learning algorithms (such as HistGradientBoosting) are fundamentally bounded by the distribution of failure patterns present in their training data. If future operational months or unmonitored deployment zones introduce:
- Previously unseen combinations of telemetry metrics,
- New firmware versions or differing reporting cadences,
- Rare hardware degradation modes that did not appear in historical labels,

the supervised model may assign low risk ($P \approx 0.05$) to an anomalous asset simply because its signature does not match past training examples.

However, an anomaly detector must **never** claim:
> *"Novel implies faulty."*

Rather:
> *"Novel indicates that an asset's telemetry pattern diverges significantly from the established fleet distribution."*

## Empirical Hypothesis
Deploying an unsupervised anomaly detector (Isolation Forest) trained strictly on historical pre-decision fleet telemetry ($t < T$):
1. Quantifies the degree of telemetry atypicality without relying on proxy labels.
2. Characterizes whether novelty reflects true operational failure vs data-quality artifacts or unusual hardware configurations.
3. Provides an independent evidence signal to cross-check supervised ML predictions.

## Methodology & Unsupervised Architecture
- **Model**: `sklearn.ensemble.IsolationForest` (100 estimators, contamination = 0.05, random_state = 42).
- **Feature Space**: The 31 baseline telemetry features standardized across the historical fleet.
- **Strict Temporal Training**:
  - For each decision week $T$, the isolation forest is fitted strictly on pre-decision historical weeks ($t < T$). Zero test-period or future observations are accessible.
- **Scoring Function**:
  $$\text{score}_{\text{raw}} = - \text{decision\_function}(X)$$
  Mapped to a normalized $[0.0, 1.0]$ percentile range as `feat_novelty_score`.
  Binary threshold `is_novel_anomaly = 1` if raw score exceeds the 95th percentile ($\alpha = 0.05$).

## Novelty vs Data Quality Forensic Check
Section 16 requires an explicit investigation into the empirical drivers of novelty. We inspect whether flagged anomalies reflect:
- **A. True Operational Degradation**: Extreme offline duration, backhaul collapse, or severe packet loss.
- **B. Unusual Gateway Type**: Rare antenna types (e.g. Panel 7dBi, $0.7\%$ of fleet) or unusual site types.
- **C. Telemetry Silence / Missingness**: Extended missing reporting hours.
- **D. Lifecycle Transitions**: Newly commissioned or decommissioning gateways.
- **E. Benign Data Artifacts**: High CPU load without packet loss.

## Overlap Breakdown: Supervised ML vs Unsupervised Novelty
We evaluate the four-quadrant confusion matrix between Supervised HGB Top-15 Dispatches and Unsupervised Novelty Top-15 Outliers:
1. **Both Catch ($HGB \cap Novelty$)**: High-confidence severe failures exhibiting both extreme supervised risk and global atypicality.
2. **HGB Catches, Novelty Misses ($HGB \setminus Novelty$)**: Familiar, textbook failure modes (e.g., standard backhaul disconnection loops) that are common in historical data and thus not statistically "novel."
3. **Novelty Catches, HGB Misses ($Novelty \setminus HGB$)**: Out-of-distribution telemetry patterns (e.g., extreme memory exhaustion or rare sensor spikes) that the supervised model ignored.
4. **Neither Catches**: Standard healthy fleet operating within normal parameters.

## Results & Findings

### Forensic Characterization: Novel Anomalies vs Normal Fleet

| Diagnostic Metric | Novelty Outliers (`is_novel_anomaly = 1`) | Normal Fleet (`is_novel_anomaly = 0`) | Contrast Ratio |
| :--- | :---: | :---: | :---: |
| **Fleet Prevalence** | **5.00%** ($N=224$ in eval window) | 95.00% | — |
| **Mean Missing Telemetry Ratio** | **0.586** (98.4 missing hours/wk) | **0.114** (19.2 missing hours/wk) | **$5.14\times$ Elevated** |
| **Mean Offline Duration** | **91.83 hours / week** | **3.51 hours / week** | **$26.16\times$ Elevated** |
| **Mean Reboot Count** | **68.02 reboots / week** | **1.34 reboots / week** | **$50.76\times$ Elevated** |
| **Correlation with Target Deficit ($r$)** | **+0.6814** | — | Strong Positive Association |

### Operational Impact of Integrating Novelty into Model (E-N01)

| Evaluation Metric | Baseline V1 | Baseline + Novelty Score | Impact |
| :--- | :---: | :---: | :---: |
| **16-Week Total Operational Cost** | **€128,400** | **€132,000** | **+€3,600 (Worse)** |
| Technician Visit Cost (€380/visit) | €91,200 | €91,200 | Fixed budget (240 visits) |
| Missed Fault Penalty Cost (€600/wk) | €37,200 | €40,800 | +€3,600 penalty increase |
| **Precision@15** | 30.83% | 30.42% | -0.41% drop |
| **Recall on Fault-Weeks** | 83.33% | 81.72% | -1.61% drop |
| Wasted Visits | 166 | 167 | +1 wasted truck roll |
| Unaddressed Fault Episodes | 62 | 68 | +6 unaddressed episodes |
| **Temporal CV Total Cost** | €144,900 | €146,700 | +€1,800 degradation |
| **Gateway-Disjoint CV Total Cost** | €727,500 | €728,700 | +€1,200 degradation |

## Interpretation & Operational Insights
1. **Forensic Cause of Degradation**: Although novelty correlates with severe deficits ($r = +0.6814$), it also aggressively flags benign telemetry missingness (e.g. communication pauses without meter read failures) and specialized hardware configurations (such as Yagi 9dBi nodes with 85x packet volume).
2. **Dispatch Distortion**: When novelty is incorporated into the supervised model, it diverts dispatches toward unpopulated/partially communicating gateways rather than active smart-meter collection collapses, causing 6 additional unaddressed fault episodes and increasing total operational cost to **€132,000**.
3. **Scientifically Grounded Rejection**: This directly answers Section 16 of the authority prompt: Unsupervised novelty detects data-quality missingness and structural configurations rather than pure physical faults.

## Limitations
1. **Lack of Directionality**: Isolation Forest measures multidirectional distance from cluster centers. Both "exceptionally good" telemetry (0 disconnections, 100% uptime, zero packet drops) and "exceptionally bad" telemetry can be flagged as novel.
2. **Sensitivity to Feature Scaling**: Without careful imputation and clipping, isolated extreme telemetry values dominate the tree splits.

## Decision
**REJECTED FROM PRIMARY DISPATCH MODEL**. Unsupervised novelty increases operational cost (+€3,600) and degrades recall (-1.61%). It is retained exclusively as an auxiliary offline monitoring alert for data-quality audits and distribution drift tracking.
