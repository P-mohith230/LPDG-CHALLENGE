# LPDG Gateway Intelligence Platform — Operational Walkthrough

## Overview
This document guides field-operations dispatchers, lead engineers, and reviewers through the 7 distinct views of the **LPDG Gateway Intelligence Platform**.

To launch the dashboard locally:
```powershell
streamlit run app/app.py
```

---

## Page-by-Page Walkthrough

### 1. Overview & Control Center
- **System Status**: Displays operational status (`ONLINE`) and active model (`Selected Production Architecture: C3`).
- **Week Selector**: Dropdown to toggle between the 8 official competition weeks (`2026-02-02` to `2026-03-23`).
- **Executive KPIs**:
  - *Weekly Visit Capacity*: 15 visits / week (€5,700 weekly rate).
  - *Gateways Above Operational Threshold*: Count of gateways with predicted risk $p \ge 0.50$ (operational target deficit threshold).
  - *Mean Priority Risk*: Average failure probability across the Top 15 dispatches for the active week.
  - *Avoided Deficit Penalties*: Avoided penalty (€600 per intercepted fault).
- **3D Operational Fleet View**:
  - Rotate, pan, and zoom using standard orbit mouse controls.
  - Observe elevation: Higher nodes represent higher predicted risk.
  - Hover over any node to reveal Gateway ID, Risk Probability, and Elevation.
  - Click any node to focus the camera and view its details in the Quick Inspector.
- **Top 15 Priority Dispatches Table**: Ranks 1 to 15 with risk percentages, status tiers, and diagnostic explanations.

### 2. Gateway Explorer
- **Fleet Search & Filters**: Search by Gateway ID or filter by antenna hardware (`Yagi 9 dBi`, `Omni 3 dBi`, etc.) and priority dispatch status.
- **Fleet Catalog Table**: Comprehensive asset list with antenna models, associated smart meters, and risk statuses.
- **Individual Asset Inspector**: Deep dive into any selected gateway showing hardware details, diagnostic attribution, and 2D historical collection read-ratio curves.

### 3. Visit Prioritization
- **Official Dispatches**: 15 prioritized visits for the chosen week under the C3 decision policy.
- **2-Week Cooldown Enforcement**: Visual documentation of cooldown suppression preventing repeat visits to chronic unresolved faults.
- **Multi-Week Dispatch Timeline**: 8-week scatter plot showing rank distribution and multi-visit frequency.
- **What-If Exploration Sandbox**:
  - Prominent banner: `EXPLORATION ONLY — NOT OFFICIAL SUBMISSION`.
  - Adjust the hypothetical capacity slider (5 to 30 visits/week) to explore simulated cost trade-offs in memory without modifying `predictions.csv`.

### 4. Model Intelligence
- **Decision Pipeline Flow**: Visual step-by-step diagram from raw telemetry and temporal firewalling to deterministic ranking.
- **Explicit 32 C3 Feature Breakdown**:
  - 29 Baseline Engineered Features (Availability, Stability, Radio, Static).
  - 3 Gateway Self-Baseline Features ($z_{\text{offline}}$, $z_{\text{missing}}$, and composite anomaly score).
- **Physical Domain Invariants**: Explains wall-clock peak offline bounding and physical hourly conservation.
- **Permutation Feature Importance**: Horizontal bar chart showing relative importance across feature families evaluated on the 5-fold gateway-disjoint CV split.
- **Diagnostic Failure Signatures**: Table of the 5 grounded signatures from `SIGNATURE_REGISTRY`.

### 5. Economic Analysis
- **Dual-Horizon Financial Panels**:
  - *Section A (Official Challenge)*: 8 scored weeks, 120 total visits, €45,600 fixed visit component, hidden ground truth evaluation.
  - *Section B (Historical Development Benchmark)*: 16 evaluation weeks, 240 visits, €91,200 fixed visit cost, evaluated against proxy targets ($\text{read\_ratio} < 0.50$).
  - Stacked cost comparison chart: Visualizing €115,200 C3 total cost vs €128,400 Baseline V1 and €164,400 3-Sigma.
- **Episode Interruption Economics**: Explanation of repeat-visit suppression and penalty reduction.

### 6. Innovation Lab
- **Configuration Trade-off Analysis**:
  - Interactive 2D scatter plot: 16-Week Historical Benchmark Total Cost (€) vs Unseen-Gateway Spatial CV PR-AUC across C0–C10.
  - Comparative reconciliation table showing feature counts, unaddressed faults, spatial PR-AUC, and fold standard deviation.
  - Clear architectural selection rationale for C3.

### 7. System Architecture
- **Layered Boundary Diagram**: Visualizing the strict separation between the Streamlit software layer (`app/`), precomputed artifacts, and the frozen ML pipeline (`src/`).
- **Engineering Principles**: Highlights zero pipeline destabilization, isolated WebGL component, and zero infrastructure bloat.
- **Data Provenance Table**: Explicit mapping connecting every UI section to its authoritative repository source.

---

## Operational Disclaimers
1. **Official Competition Predictions**: Stored in `predictions.csv`. The dashboard reads this file in read-only mode and never alters its contents or SHA256 checksum.
2. **Demo Mode**: When toggled in the sidebar, synthetic data is used for demonstration purposes with a persistent disclosure banner.
