# Final Innovation Decision & Promoted Architecture

## Authority & Evaluation Context
This document records the definitive architectural promotion and rejection decisions for the **Innovation Phase** of the LPDG Innovation Hub Selection Challenge 2026.

All candidate innovations were evaluated strictly under the **Unified 16-Week Economic Benchmark Window** (`2025-10-06` to `2026-01-19`, exactly 240 technician dispatches, €380/visit, €600 unaddressed fault penalty/week) against the frozen reference standard **`BASELINE_V1`** (€128,400 total operational cost, 30.83% Precision@15, 83.33% Recall, 52 repeat visits).

## Innovation Evaluation Summary

### 1. Innovation 1: Failure Progression / Deterioration Score
- **Concept**: Compares trailing 7-day telemetry $[T - 7\text{d}, T)$ against prior 21-day baseline $[T - 28\text{d}, T - 7\text{d})$ to compute temporal trend deltas, surge ratios, and a bounded composite deterioration score ($D \in [0.0, 1.0]$).
- **Engineering Note**: The 7-day recent and 21-day prior baseline window durations are empirical candidate engineering choices, not official challenge specifications.
- **Evidence**: Captures accelerating outages and distinguishes acute failure trajectories from stable chronic noise, cutting temporal CV fold cost variance by 60%.
- **Status**: **[PROMOTED AS ANALYTICAL MONITOR & EXPLANATION FEATURE]**

### 2. Innovation 2: Operational Degradation Signature Engine
- **Concept**: 5 domain-grounded diagnostic rules evaluating backhaul collapse, hardware power-cycle surges, silence blackouts, RF downlink degradation, and compound multi-domain failure states.
- **Evidence**: Demonstrates strong relative risk multiplication ($9.41\times$ to $20.63\times$) for next-week collection deficits. Including raw signature scores inside GBDT splits introduced slight tree collinearity (+€1,800 cost in C2).
- **Status**: **[PROMOTED AS PRIMARY EXPLANATION & DIAGNOSTIC TAG ENGINE]** (Incorporated directly into `predictions.csv` reason generator).

### 3. Innovation 3: Gateway-Specific Historical Baseline
- **Concept**: Normalizes recent 7-day behavior against an asset's own 28-day operating distribution with a 72-hour cold-start guard.
- **Engineering Note**: The 28-day history length and 72-hour fallback are empirical candidate engineering choices, not official challenge specifications.
- **Evidence**: Generates the single largest standalone economic gain of the Innovation Phase: reduces 16-week benchmark cost from €128,400 down to **€115,200** (-€13,200), boosts Recall from 83.33% to **89.25%**, cuts unaddressed faults from 62 to **40**, and drives spatial Gateway-Disjoint CV PR-AUC from 0.6777 to **0.7658** (+0.0881 gain on completely unseen gateways).
- **Status**: **[PROMOTED AS CORE CHAMPION FEATURE FAMILY]**

### 4. Innovation 4: Risk × Deterioration Priority Engine
- **Concept**: Decouples static ML risk probability $P$ from dynamic deterioration rate $D$, prioritizing "Critical Accelerating" and "Early-Warning Emerging" assets into the weekly top-15 quota.
- **Evidence**: Evaluated across 4 formulations (multiplicative, additive, Borda, quadrant boost). While Borda cut repeat visits from 52 to 50 and quadrant boost intercepted faults at Week -1, ranking adjustments altered probability calibration, incurring €2,400 higher penalty costs than pure C3 risk ranking (€117,600 vs €115,200).
- **Status**: **[EVALUATED CANDIDATE; RETAINED AS ALTERNATIVE PRIORITY MODULE]**

### 5. Innovation 5: Unsupervised Fleet Novelty / OOD Detector
- **Concept**: Isolation Forest anomaly scoring fitted strictly on historical pre-decision data ($t < T$).
- **Evidence**: Forensics reveal that unsupervised novelty primarily flags telemetry missingness and unusual antenna configurations (Yagi 9dBi) rather than operational failure. Standalone novelty dispatch increases 16-week benchmark cost by +€3,600 (€132,000) and drops recall.
- **Status**: **[RETAINED AS AUXILIARY TELEMETRY DRIFT / DATA QUALITY AUDITOR; REJECTED FROM PRIMARY DISPATCH]**

## Final Architecture Decision: C3 vs C10 Resolution

Under the project's explicit three-tier decision hierarchy:
1. **Primary Criterion (Operational Cost)**:
   - **C3**: **€115,200** (Visit: €91,200, Penalties: €24,000 | 40 unaddressed faults)
   - **C10**: **€117,600** (Visit: €91,200, Penalties: €26,400 | 44 unaddressed faults)
   - **Verdict**: **C3 saves €2,400 more than C10**, leaving 4 fewer unaddressed collection deficits.
2. **Secondary Criterion (Generalization & Temporal Stability)**:
   - **Gateway-Disjoint CV (Unseen Gateways)**: C3 achieves PR-AUC of **0.7658** and fold cost standard deviation of **€1,489** (total €720,900), outperforming C10 (PR-AUC 0.7438, fold std €2,590, total €723,300).
   - **Temporal Walk-Forward CV (Quarterly Generalization)**: C3 achieves PR-AUC of **0.8465** and total cost of **€132,300** (fold std €3,608), outperforming C10 (PR-AUC 0.8297, total cost €134,100, fold std €3,658).
   - **Verdict**: **C3 demonstrates superior generalization and lower variance on both spatial and temporal splits**.
3. **Tertiary Criterion (Complexity, Interpretability & Reproducibility)**:
   - **Complexity**: C3 adds exactly 3 self-history baseline features with pure calibrated probability ranking. C10 requires heuristic quadrant threshold tuning ($\alpha, \beta$ weights and class boundaries).
   - **Interpretability**: C3 preserves full interpretability by integrating Failure Signatures (`SIG_01`–`SIG_05`) and Deterioration indicators directly into the `reason` string generator.
   - **Verdict**: **C3 is strictly leaner, more reproducible, and equally interpretable**.

**Definitive Architectural Decision**:
**Candidate C3 is promoted as the Champion Production Architecture.**
C10 is formally documented as a validated alternative priority architecture. Failure Signatures and Deterioration Dynamics serve as the primary diagnostic explanation layer in the official submission.

## Final Promoted Candidate Architecture (C3 Champion Pipeline)

```text
RAW TELEMETRY + GATEWAY MASTER METADATA
                  │
                  ▼
DATA QUALITY & LIFECYCLE FIREWALL
(Mask 12 future mid-2026 installs & 12 decommissioned gateways)
                  │
                  ▼
FEATURE ENGINEERING ENGINE (t < Monday 00:00:00 UTC)
├── 29 Audited Baseline Features (Availability, Stability, Radio, Static Context)
└── 3 Gateway-Specific Self-History Baseline Features (28d History, 72h Cold-Start Guard)
    ├── feat_gw_relative_anomaly_score
    ├── feat_gw_z_offline
    └── feat_gw_z_missing
                  │
                  ▼
SUPERVISED RISK ESTIMATOR
(HistGradientBoostingClassifier, balanced, lr=0.05, max_depth=4, 32 features)
                  │
                  ▼
OPERATIONAL COOLDOWN POLICY
(Enforce 2-Week Post-Visit Ineligibility Window)
                  │
                  ▼
DETERMINISTIC TOP-15 SELECTION
(Strict Lexicographical Ordering: -risk_score, gateway_id)
                  │
                  ▼
DIAGNOSTIC EXPLANATION GENERATOR
(Grounded telemetry evidence + Domain Failure Signature tags <= 300 characters)
                  │
                  ▼
predictions.csv (120 rows, 8 evaluation weeks, exactly 15 visits/week)
```

## Quantitative Performance Comparison

| Evaluation Dimension | 3-Sigma Baseline | Frozen Baseline V1 (C0) | Promoted Champion (C3) | Evaluated Candidate (C10) | Champion Impact vs Base V1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **16-Week Total Cost** | €164,400 | €128,400 | **€115,200** | €117,600 | **-€13,200 (-10.28%)** |
| **Visit Cost (€380/visit)** | €91,200 | €91,200 | **€91,200** | €91,200 | €0 (Exact 240 visits) |
| **Penalty Cost (€600/fault)** | €73,200 | €37,200 | **€24,000** | €26,400 | **-€13,200 (-35.48%)** |
| **Unaddressed Faults** | 122 | 62 | **40** | 44 | **-22 faults (-35.48%)** |
| **Intercepted Faults** | 250 | 310 | **332** | 328 | **+22 faults (+7.10%)** |
| **Precision@15** | 25.83% | 30.83% | **32.92%** | 32.50% | **+2.09%** |
| **Recall on Severe Faults** | 67.20% | 83.33% | **89.25%** | 88.17% | **+5.92%** |
| **Repeat Visits** | 50 | 52 | **53** | 52 | +1 repeat visit |
| **Temporal CV PR-AUC** | -- | 0.7759 | **0.8465** | 0.8297 | **+0.0706** |
| **Temporal CV Cost (€)** | -- | €144,900 | **€132,300** | €134,100 | **-€12,600** |
| **Temporal CV Fold Std (€)**| -- | €7,229 | **€3,608** | €3,658 | **-50.1% variance** |
| **Gateway CV PR-AUC** | -- | 0.6777 | **0.7658** | 0.7438 | **+0.0881** |
| **Gateway CV Cost (€)** | -- | €727,500 | **€720,900** | €723,300 | **-€6,600** |
| **Gateway CV Fold Std (€)** | -- | €2,245 | **€1,489** | €2,590 | **-33.7% variance** |

## Non-Negotiable Scientific Disclaimers
1. **Operational Proxy Limitation**: The supervised target $Y(g, k+1) = \mathbb{I}(\text{read\_ratio} < 0.50)$ is an empirical proxy for severe operational collection failure. It is **not** the hidden official hardware defect label.
2. **Economic Benchmarking Disclaimer**: The €115,200 champion and €128,400 baseline cost figures represent retrospective evaluations within the project's historical simulator under identical assumptions, **not** an official challenge score.
3. **Deterministic Reproducibility**: The complete pipeline executes deterministically with fixed random seeds (42), strict tie-breaking, and zero runtime external dependencies.

