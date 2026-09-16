"""Model Intelligence & Observability page.

Explains the C3 architecture visually:
- Pipeline flow from telemetry to top 15 dispatches.
- Explicit 32 features (29 baseline + 3 gateway self-baselines).
- Physical domain invariants.
- 5 registered failure signatures from SIGNATURE_REGISTRY.
- Native permutation importance on 5-fold gateway-disjoint CV split.
"""

from __future__ import annotations

import sys
from pathlib import Path

_app_dir = str(Path(__file__).resolve().parent.parent)
_project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path = [p for p in sys.path if p != _app_dir]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


import plotly.express as px
import streamlit as st

from app.services.feature_service import FeatureService
from app.services.model_service import ModelService
from app.utils.state import is_demo_mode


def render() -> None:
    """Render the Model Intelligence page."""
    demo = is_demo_mode()
    meta = ModelService.get_c3_architecture_metadata()
    feature_counts = FeatureService.get_feature_counts()
    families = FeatureService.get_baseline_feature_families()
    gw_baselines = FeatureService.get_gateway_baseline_features()
    invariants = FeatureService.get_physical_invariants()
    signatures = FeatureService.get_failure_signatures()
    importance_df = ModelService.get_permutation_importances()

    st.markdown("## 🧠 Model Intelligence & Pipeline Architecture")
    st.caption("Detailed observability into the selected production architecture (C3).")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Architecture Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model Family", meta["model_type"], "Gradient Boosted Trees")
    with col2:
        st.metric("Total Production Features", f"{feature_counts['total_c3_features']} Features", "29 Base + 3 Self-Baselines")
    with col3:
        st.metric("Cooldown Suppression", "2 Weeks", "Enforced post-visit")
    with col4:
        st.metric("Tie-Breaking", "Deterministic", "Secondary sort: gateway_id")

    st.markdown("---")

    # Pipeline Flow Chart
    st.markdown("### 🔄 End-to-End Decision Flow")
    st.code(
        """
Raw Telemetry (ts < T) ──► Temporal Firewall Validation
                                │
                                ▼
Feature Matrix Extraction (29 Baseline + 3 Gateway Self-Baselines = 32 Features)
                                │
                                ▼
HistGradientBoosting Classifier (Calibrated Predicted Risk Probability)
                                │
                                ▼
2-Week Cooldown Filter (Suppress gateways visited in week k-1 or k-2)
                                │
                                ▼
Deterministic Lexicographical Ranking (Primary: -score, Secondary: gateway_id)
                                │
                                ▼
Top 15 Official Technician Dispatches (predictions.csv)
        """,
        language="text",
    )

    st.markdown("---")

    # Explicit 32 C3 Features
    st.markdown("### 🧬 Explicit 32 C3 Feature Breakdown")
    st.markdown(
        "The production pipeline strictly uses **32 features**: **29 baseline/engineered features** "
        "and **3 gateway self-baseline features**. It does not incorporate experimental features from other candidates."
    )

    fcol1, fcol2 = st.columns(2)

    with fcol1:
        st.markdown("#### 1. Baseline Engineered Features (29 Features)")
        with st.expander(f"Availability & Missingness ({len(families.get('availability', []))} features)", expanded=True):
            st.write(families.get("availability", []))

        with st.expander(f"Stability & Reboots ({len(families.get('stability', []))} features)"):
            st.write(families.get("stability", []))

        with st.expander(f"Radio Front-End ({len(families.get('radio', []))} features)"):
            st.write(families.get("radio", []))

        with st.expander(f"Static Asset Characteristics ({len(families.get('static', []))} features)"):
            st.write(families.get("static", []))

    with fcol2:
        st.markdown("#### 2. Gateway Self-Baselines (3 Features)")
        st.info(
            "Different gateways exhibit vastly different normal operating levels due to antenna gain "
            "(Yagi 9dBi averages 389k pkts/wk vs 4.6k for Omni 3dBi). "
            "Self-baselines evaluate each asset against its own 28-day operating history."
        )
        st.write(gw_baselines)

        st.markdown("#### 3. Physical Domain Invariants")
        for inv_name, inv_desc in invariants.items():
            st.write(f"- **{inv_name}**: `{inv_desc}`")

    st.markdown("---")

    # Native Permutation Importance
    st.markdown("### 📊 Permutation Feature Importance")
    st.caption("Evaluated on 5-fold gateway-disjoint cross-validation split using native scikit-learn inspection (no external SHAP dependency).")

    fig = px.bar(
        importance_df,
        x="relative_importance",
        y="feature_family",
        orientation="h",
        title="Relative Permutation Importance Across Feature Families (Gateway-Disjoint CV)",
        labels={"relative_importance": "Relative Importance", "feature_family": "Feature Family"},
        color="relative_importance",
        color_continuous_scale="Blues",
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="#1E222D",
        plot_bgcolor="#131722",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=30, r=30, t=40, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Grounded Failure Signatures
    st.markdown("### 🩺 Diagnostic Failure Signatures")
    st.caption("Independent rule-based evidence layer used for explainable dispatch reasons (from SIGNATURE_REGISTRY).")

    sig_records = []
    for sig in signatures:
        sig_records.append({
            "Signature ID": sig.signature_id,
            "Signature Name": sig.name,
            "Family": sig.family,
            "Description": sig.description,
            "Weight": f"{sig.weight:.2f}",
        })
    st.dataframe(sig_records, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render()
