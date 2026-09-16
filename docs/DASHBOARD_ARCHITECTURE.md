# LPDG Gateway Intelligence Platform — Architecture & Technical Specifications

## 1. Architectural Purpose & Boundaries
The **LPDG Gateway Intelligence Platform** is an operational decision-support and machine learning observability system built for utility engineering and field-dispatch operations teams.

It is strictly an interactive presentation and decision-support layer (`app/`) that sits on top of the already validated and frozen **Candidate C3 Machine Learning Pipeline Core** (`src/`).

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STREAMLIT DECISION SUPPORT LAYER                      │
│                                  (app/)                                     │
│                                                                             │
│   Overview    Gateway Explorer   Visit Prioritization   Economic Analysis   │
│   Model Intel Innovation Lab     System Architecture                        │
│                                                                             │
│   Components: Three.js WebGL (3D Fleet View), Plotly 2D Trends, KPI Cards   │
│   Services:   PredictionService, GatewayService, EconomicService            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Read-Only Consumer Interface)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PRECOMPUTED ARTIFACTS & RESULTS                        │
│                                                                             │
│   predictions.csv            (SHA256: f2712079... verified byte-identical)  │
│   experiment_results.json    (16-Week Historical Benchmark Results C0-C10)  │
│   gateway_master.csv         (Hardware & Installation Catalog)              │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ (Generates Submission Outputs)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                  FROZEN C3 MACHINE LEARNING PIPELINE CORE                   │
│                                  (src/)                                     │
│                                                                             │
│   src/prediction/inference.py    -> Generates official predictions.csv      │
│   src/models/trainer.py          -> HistGradientBoosting Model Core         │
│   src/models/decision_policy.py  -> 2-Week Cooldown & Deterministic Ranking │
│   src/features/builder.py        -> 29 Baseline Engineered Features         │
│   src/features/gateway_baseline  -> 3 Gateway Self-Baseline Features        │
│   src/evaluation/cost_simulator  -> Economic Cost Simulation Function       │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▲
                                       │ (Completely Independent Runner)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                    OFFICIAL COMPETITION ENTRY POINT                         │
│                                                                             │
│   python run.py                  -> Generates official predictions.csv      │
│   python validate_submission.py  -> Verifies schema, ranks, constraints     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Inviolable Pipeline Decoupling
1. **Competition Immutability**:
   - The competition entry point `python run.py` executes completely independently of the Streamlit dashboard.
   - The submission validator `python validate_submission.py predictions.csv` continues returning exit code 0.
   - `predictions.csv` SHA256 checksum remains byte-identical (`f27120799bd55bde34508299c411f763d54e7766e266ac54c0619307a6d54608`).
2. **Zero Training on UI Load**:
   - The dashboard does not retrain models, extract raw features from scratch, or re-run inference loops.
   - It reads authoritative precomputed artifacts and structured predictions.

---

## 3. Strict Horizon Separation
The application structurally and visually enforces a firewall between two distinct horizons:

| Dimension | Official Challenge Constraints | Historical Development Benchmark |
| :--- | :--- | :--- |
| **Time Window** | **8 Scored Weeks** (`2026-02-02` to `2026-03-23`) | **16 Historical Weeks** (`2025-10-06` to `2026-01-19`) |
| **Visit Budget** | 15 visits/week = **120 total visits** | 15 visits/week = **240 total visits** |
| **Fixed Cost Component** | $120 \times €380 = \mathbf{€45,600}$ | $240 \times €380 = \mathbf{€91,200}$ |
| **Evaluation Target** | Hidden Ground Truth (Official Portal Scoring) | Historical Operational Proxy Target ($\text{read\_ratio} < 0.50$) |
| **Benchmark Figures** | *N/A (Hidden official evaluation)* | **3-Sigma**: €164,400<br>**Baseline V1 (C0)**: €128,400<br>**Candidate C10**: €117,600<br>**Selected Production Architecture (C3)**: €115,200 |
| **Display Boundary** | Overview, Visit Prioritization, Submission integrity | Exclusively in Economic Analysis and Innovation Lab |

---

## 4. Three.js / WebGL Integration Architecture
Built in accordance with the MengTo `threejs` and `webgl-3d-object` skill best practices:
- **Renderer Setup**:
  - `THREE.WebGLRenderer` configured with `powerPreference: "high-performance"`, `antialias: true`, `alpha: false`.
  - Color space: `ACESFilmicToneMapping` with exposure 1.1; sRGB output.
- **Visual Encoding Philosophy**:
  - **Primary Encoding**: **Elevation (Y-axis)** directly reflects predicted failure risk $p \in [0, 1]$ ($y = p \times 14.0$). High-risk nodes tower above the baseline ground plane.
  - **Secondary Encoding**: **Color** mapping into calm industrial tiers:
    - Slate Blue (`#3B82F6`): Normal fleet range ($p < 0.30$).
    - Warm Amber (`#F59E0B`): Moderate risk ($0.30 \le p < 0.70$).
    - Coral Crimson (`#EF4444`): High / Critical risk ($p \ge 0.70$).
  - **Orbital Priority Reticle**: The 15 prioritized dispatches for the week receive a purple orbital wireframe indicator (`#8B5CF6`).
  - **Animation**: Subtle sine breathing pulse applied *only* to the currently selected or prioritized nodes.
- **Controls & Pointer Interaction**:
  - `THREE.OrbitControls` with damping enabled (`dampingFactor: 0.05`), distance constraints (`minDistance: 10`, `maxDistance: 120`), and polar angle lock to prevent underground camera dipping.
  - Pointer raycasting on `pointermove` showing instant tooltip (Gateway ID, Risk Probability, Elevation).
  - Click-to-focus: Camera controls target eases directly to the clicked node.
- **Topological Layout Labeling**:
  - Explicitly labeled: `"Operational Network / Fleet View — Abstract topology, not geographic coordinates."`
  - No synthetic maps or fake coordinates.

---

## 5. Software Layer Structure

```text
app/
├── app.py                          # Streamlit application entry point & navigation router
├── pages/
│   ├── overview.py                 # Control Center: KPIs, 3D Operational Fleet View, Top 15 Dispatches
│   ├── gateway_explorer.py         # Gateway Explorer: Fleet search, temporal risk trends, telemetry histories
│   ├── visit_prioritization.py     # Operations: 15-visit capacity, 2-wk cooldown, isolated What-If simulation
│   ├── model_intelligence.py       # ML Pipeline: 32 C3 features (29+3), C3 flow, permutation importance
│   ├── economic_analysis.py        # Financials: Official Challenge Constraints vs Historical Development Benchmark
│   ├── innovation_lab.py           # Configuration Trade-off Analysis: C0–C10 empirical trade-offs
│   └── system_architecture.py      # Architecture: Decoupling Streamlit software layer from C3 ML pipeline
├── components/
│   ├── three_scene.py              # Three.js WebGL canvas generator (MengTo skill patterns)
│   ├── kpi_cards.py                # Metric summary display cards
│   ├── risk_chart.py               # 2D temporal risk trend & distribution plots (Plotly)
│   ├── gateway_table.py            # Formatted data tables with status badges
│   ├── gateway_detail.py           # Gateway operational inspector panel
│   ├── timeline.py                 # Multi-week historical trend charts
│   └── economic_panel.py           # Cost waterfall & penalty savings comparison
├── services/
│   ├── prediction_service.py       # Reads & queries predictions.csv (ranks, scores, reasons)
│   ├── feature_service.py          # Extracts 32 C3 features (29 baseline + 3 gateway self-baselines)
│   ├── gateway_service.py          # Gateway catalog & status aggregator (local data + synthetic demo fallback)
│   ├── economic_service.py         # Cost simulator queries (€380 visits, €600 unaddressed faults)
│   └── model_service.py            # C3 model architecture metadata & C0–C10 experiment results
├── data/
│   ├── adapters.py                 # Adapters bridging existing src/ artifacts to app cleanly
│   └── demo_data.py                # Sanitized synthetic gateway records for standalone demo mode
└── utils/
    ├── formatting.py               # Currency (€), percentage, and timestamp formatting
    ├── state.py                    # Session state management (selected week, selected gateway)
    └── config.py                   # App theme, colors, capacity constants
```

---

## 6. Zero-Infrastructure & Anti-Hallucination Guarantees
- **No External Infrastructure**: No databases, APIs, authentication, Docker, or external LLM dependencies.
- **Provenance Grounding**:
  - Official Dispatches $\to$ `predictions.csv`
  - Challenge Constants $\to$ `src/utils/config.py`
  - 32 C3 Features $\to$ `src/features/builder.py` & `src/features/gateway_baseline.py`
  - 5 Failure Signatures $\to$ `src/intelligence/failure_signatures.py` (`SIGNATURE_REGISTRY`)
  - 16-Week Benchmarks $\to$ `scratch/innovation_experiment_results.json`
- **Missing Data Policy**: If a metric or telemetry record is unavailable, the UI states `"Data unavailable from workspace"` rather than manufacturing an approximation.
- **Isolated Demo Mode**: When toggled, a persistent warning banner is displayed: `[DEMO MODE: Synthetic Data — Not Official Challenge Data]`.
