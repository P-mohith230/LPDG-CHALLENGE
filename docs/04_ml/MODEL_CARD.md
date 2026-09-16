# Machine Learning Model Card: LPDG Dispatch Ranker
**LPDG Innovation Hub Selection Challenge 2026**  
*Model Governance, Architecture, Intended Use, Training Regimen, and Limitations*

---

## Model Card Governance Status
- **Current Model Status**: `TEMPLATE — SKELETON SPECIFICATION (MODEL NOT YET TRAINED)`
- **Model Version**: Pending final model selection (e.g. `v0.1-candidate`).
- **Date**: 15 September 2026.
- **Model Authors**: NEXORA 2026 Selection Candidate.
- **Primary Optimization Objective**: Total Operational Cost Minimization under LPDG €380/€600 Economic Protocol.

---

## 1. Model Details

### 1.1 Model Overview
- **Architecture**: `[PENDING EXPERIMENTAL EVALUATION — LightGBM / CatBoost / Cost-Calibrated Ranker]`
- **Model Class**: Supervised Learning / Learning-to-Rank.
- **Input Modality**: Multimodal tabular telemetry (57 sensor streams) + static asset metadata (`gateway_master.csv`).
- **Output Target**: Weekly failure risk score / priority ranking for top-15 dispatch selection.
- **Prediction Cadence**: Weekly batch prediction evaluated at Monday 00:00:00 UTC for 8 consecutive scoring weeks.

### 1.2 Underlying Framework & Dependencies
- Python Version: `3.13.5` (pinned).
- Key Libraries: `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `lightgbm` / `catboost`.
- Execution Environment: Single CPU machine, offline execution, < 4 GB RAM footprint.

---

## 2. Intended Use & Operational Context

### 2.1 Intended Use
- **Primary Use Case**: Prioritizing 15 physical site visits per week for utility maintenance technicians managing a fleet of ~320 LoRaWAN smart utility gateways.
- **Operational Target Audience**: Utility Operations Manager (providing human-interpretable diagnosis reasons under 300 characters).

### 2.2 Out-of-Scope & Prohibited Use
- Real-time second-by-second alerting (model is designed for weekly operational planning).
- Fully automated autonomous dispatch without human technician oversight.
- Direct extrapolation to non-German utility cellular networks without baseline recalibration.

---

## 3. Training Data & Pipeline Protocol

### 3.1 Training Dataset
- **Sources**: `telemetry/` partitions (August 2025 – January 2026), `gateway_master.csv`, `field_visits.csv`, `meter_read_success.csv`.
- **Target Construction**: Derived from proxy ground truth without post-cutoff leakage (documented in `TARGET_DEFINITION.md`).
- **Temporal Gating**: Gated strictly before February 2026.

### 3.2 Feature Space
- Trailing window aggregations (24h, 7d, 28d) across:
  - Telemetry silence duration.
  - Reboot frequency and power-cycle attribution.
  - Backhaul disconnection frequency and differenced offline duration.
  - LoRa packet reception and CRC error ratios.
  - OS memory collapse and load average spikes.
- Full inventory tracked in `docs/03_data/FEATURE_REGISTRY.md`.

---

## 4. Evaluation & Quantitative Performance

*Note: In compliance with project guidelines, all performance metrics will be populated only after model execution in the experimental phase.*

### 4.1 Benchmark Comparison Table
| Model Description | Total Simulated Operational Cost (€) | Cost Savings vs. Baseline (€) | Mean Precision@15 | Mean Recall@15 | 5-Fold Worst-Case Cost (€) | Status |
|---|---|---|---|---|---|---|
| **Official Supplied Baseline** (`baseline_3sigma.py`) | *Pending E-11* | €0 (Reference) | *Pending* | *Pending* | *Pending* | Benchmarked |
| **Candidate Model 1** (Statistical Cooldown Ranker) | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | Candidate |
| **Candidate Model 2** (Supervised LightGBM) | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | Candidate |
| **Final Selected Model** | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | Unselected |

### 4.2 Cohort Performance Spread
- Small sites (< 100 meters): *Pending*
- Medium sites (100–300 meters): *Pending*
- Large hubs (> 300 meters): *Pending*

---

## 5. Explainability & Reason String Generation

- **Character Limit**: Strictly $\le 300$ characters enforced by `validate_submission.py`.
- **Target Audience**: Utility Operations Manager.
- **Format Schema**:
  `"[Anomaly Category]: [Specific Signal Breach] ([Observed Value] vs. [Baseline Normal]). [Operational Consequence]"`
- **Diagnostic Transparency**: Translates raw sensor deviations into operational actions (e.g., checking power supply vs. antenna realignment).

---

## 6. Known Limitations & Caveats

1. **Proxy Ground Truth Mismatch**: The model is trained on synthetic/proxy labels because LPDG's official ground truth is held private.
2. **Missing Data Ambiguity**: Prolonged telemetry silence may reflect benign maintenance rather than physical failure.
3. **Firmware Divergence**: Sensor counter mechanics vary slightly across firmware versions (`2.14` vs. `3.3.1`).
4. **Offline Constraint**: Operates purely offline without live network telemetry pinging.
