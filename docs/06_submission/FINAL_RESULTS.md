# Final Results & Performance Benchmark Report
**LPDG Innovation Hub Selection Challenge 2026**  
**Executive Benchmark Summary, Operational Cost Comparison, and Empirical Evidence**  
**Candidate Registration ID**: `23091a3286`  
**Promoted Production Architecture**: **Candidate C3 (Champion Pipeline)**  

---

## 1. Master Status & Benchmark Protocol

All figures reported in this document are derived from the unified, like-for-like **16-Week Historical Benchmark Window** (`2025-10-06` to `2026-01-19`, 4,404 gateway-weeks evaluated, 372 severe collection-deficit fault-weeks, exactly 240 technician dispatches per active strategy):
- **Fixed Visit Cost**: Exactly €380.00 per dispatch ($240 \times €380 = €91,200$).
- **Fault Penalty**: Exactly €600.00 per unaddressed severe collection-deficit gateway-week ($\text{read\_ratio} < 0.50$).
- **Episode Accounting**: Continuous multi-week outages incur penalties each week until interrupted by an on-site visit.

---

## 2. Executive Performance Summary

### Primary Operational Objective Comparison (16-Week Unified Window)

| Performance Metric | Official Baseline (`baseline_3sigma.py`) | Frozen Baseline V1 (Stage 9) | Promoted Champion (C3) | Evaluated Alternative (C10) | Champion vs Official Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Operational Cost (€)** | **€164,400** | **€128,400** | **€115,200** | **€117,600** | **-€49,200 (-29.93%)** |
| Fixed Dispatch Visit Cost (€) | €91,200 | €91,200 | €91,200 | €91,200 | €0 (Exact 240 visits) |
| Unaddressed Fault Penalty (€) | €73,200 | €37,200 | €24,000 | €26,400 | -€49,200 (-67.21%) |
| Unaddressed Fault-Weeks | 122 | 62 | 40 | 44 | -82 faults (-67.21%) |
| Intercepted Fault-Weeks | 250 | 310 | 332 | 328 | +82 faults (+32.80%) |
| **Fleet Precision@15** | 25.83% | 30.83% | **32.92%** | 32.50% | +7.09% yield |
| **Fleet Recall on Severe Faults** | 67.20% | 83.33% | **89.25%** | 88.17% | **+22.05% recall** |
| Repeat Visits (2-Wk Cooldown) | 50 | 52 | 53 | 52 | Controlled policy |
| Wasted Visits | 178 | 166 | 161 | 162 | -17 wasted dispatches |

---

## 3. Generalization & Cross-Validation Stability Range

Adhering to strict dual-axis validation (FAQ Round 2 §5.2 and §6.9):

| Validation Split Dimension | Strategy / Model | Mean Operational Cost (€) | Fold Std Dev (€) | Mean ROC-AUC | Mean PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gateway-Disjoint CV (5 Folds)** | Frozen Baseline V1 (C0) | €727,500 | €2,245 | 0.9474 | 0.6777 |
| **Gateway-Disjoint CV (5 Folds)** | **Promoted Champion (C3)** | **€720,900** | **€1,489** | **0.9675** | **0.7658** |
| **Temporal Walk-Forward CV (3 Folds)** | Frozen Baseline V1 (C0) | €144,900 | €7,229 | 0.9687 | 0.7759 |
| **Temporal Walk-Forward CV (3 Folds)** | **Promoted Champion (C3)** | **€132,300** | **€3,608** | **0.9765** | **0.8465** |

### Key Generalization Insights:
1. **Unseen Gateway Robustness**: Candidate C3 improves PR-AUC on completely unseen hardware from 0.6777 to **0.7658** (+0.0881 gain) and cuts fold standard deviation from €2,245 to **€1,489** (a 33.7% reduction in variance).
2. **Quarterly Temporal Stability**: Candidate C3 increases out-of-time temporal PR-AUC to **0.8465** and cuts fold cost standard deviation from €7,229 to **€3,608** (a 50.1% reduction in variance).

---

## 4. Empirical Discoveries Across Modeling Stages

1. **Gateway Historical Baselines (Innovation 3)**: Normalizing trailing 7d metrics against an asset's own 28d distribution is the single most powerful feature addition, eliminating static antenna confounding and delivering €13,200 in net savings.
2. **Deterioration Dynamics (Innovation 1)**: Trend deltas between trailing 7d and prior 21d windows cut temporal CV fold cost variance by 60%, distinguishing acute active trajectories from chronic benign noise.
3. **Operational Failure Signatures (Innovation 2)**: Domain heuristic patterns (`SIG_01`–`SIG_05`) demonstrate relative risks between 9.4x and 20.6x for subsequent deficits, supplying rich, compliant ($\le 300$ chars) diagnostic reason strings directly to field technicians.
4. **Rejection of Unsupervised Novelty (Innovation 5)**: Forensics revealed that Isolation Forest anomaly flags primarily capture benign missingness and high-gain Yagi antennas, increasing operational costs by +€3,600.
5. **Cooldown Physics (Stage 8)**: Enforcing a 2-week post-visit cooldown prevents 73 redundant repeat dispatches, transforming raw ML ranking from €172,200 down to €128,400 in Baseline V1.

---

## 5. Declared Limitations

1. **Sub-Weekly Micro-Outage Masking**: Features aggregate weekly behavior; mid-week outages that recover before Sunday night are not flagged until the next dispatch cycle.
2. **Static Cooldown Policy**: Cooldown duration is uniform (14 days) across all asset types, regardless of repair complexity.
3. **Proxy Target Limitation**: Models optimize for smart meter collection deficits ($\text{read\_ratio} < 0.50$), which reflects operational utility impact rather than hidden physical hardware failure labels.
