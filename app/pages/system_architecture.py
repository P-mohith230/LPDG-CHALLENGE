"""System Architecture & Software Boundary page.

Visualizes and documents the decoupling between:
1. Streamlit Presentation & Decision Support Layer (app/)
2. Frozen C3 Machine Learning Pipeline Core (src/)
3. Competition Runner & Validator (run.py, validate_submission.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

_app_dir = str(Path(__file__).resolve().parent.parent)
_project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path = [p for p in sys.path if p != _app_dir]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


import streamlit as st

from app.utils.config import PROVENANCE
from app.utils.state import is_demo_mode


def render() -> None:
    """Render the System Architecture page."""
    demo = is_demo_mode()
    st.markdown("## 🏛️ System Architecture & Software Decoupling")
    st.caption("Clear architectural boundary separating the interactive Streamlit software layer from the frozen ML core.")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Decoupling Diagram
    st.markdown("### 🧩 Layered Architectural Boundary")
    st.code(
        """
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
        """,
        language="text",
    )

    st.markdown("---")

    # Core Architectural Principles
    st.markdown("### 🛡️ Core Engineering Invariants")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 1. Zero Pipeline Destabilization")
        st.write(
            """
            - The dashboard is purely a **consumer** of generated outputs.
            - It does **NOT** retrain the model, modify feature extraction, adjust hyperparameters, or rewrite predictions.
            - `python run.py` remains completely runnable without Streamlit installed.
            """
        )

        st.markdown("#### 2. Isolated 3D Component")
        st.write(
            """
            - The Three.js WebGL canvas is isolated inside an embedded component boundary.
            - JavaScript handles geometry, camera, lighting, and pointer raycasting.
            - Python retains full control over application state, data processing, and ML results.
            """
        )

    with col2:
        st.markdown("#### 3. Zero Infrastructure Bloat")
        st.write(
            """
            - **No external database server** (works from local files and cached memory).
            - **No microservices or REST APIs**.
            - **No Docker or Kubernetes overhead**.
            - **No external cloud services or LLM calls**.
            - Designed for instant, reproducible execution on a standard laptop.
            """
        )

        st.markdown("#### 4. Strict Data Boundary")
        st.write(
            """
            - Raw challenge files (*.parquet, *.xlsx) are excluded from git.
            - The dashboard runs locally against local data when present, and seamlessly falls back to synthetic demo mode.
            """
        )

    st.markdown("---")

    # Data Provenance Table
    st.markdown("### 🗺️ Data Provenance Mapping")
    st.caption("Every metric and chart displayed in the application is traced directly to its authoritative source.")

    prov_rows = [{"Dashboard Domain": k.replace("_", " ").title(), "Workspace Source": v} for k, v in PROVENANCE.items()]
    st.dataframe(prov_rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render()
