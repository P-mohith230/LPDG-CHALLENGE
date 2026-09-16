"""Overview & Operations Control Center page.

The main operational screen providing:
- System operational status & active week selector.
- KPI metric row.
- Interactive Three.js 3D Operational Fleet View.
- Top 15 Prioritized Dispatches Table.
- Quick Gateway Inspector.
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

from app.components.gateway_detail import render_gateway_inspector
from app.components.gateway_table import render_priority_table
from app.components.kpi_cards import render_overview_kpis
from app.components.three_scene import render_three_fleet_view
from app.services.gateway_service import GatewayService
from app.services.prediction_service import PredictionService
from app.utils.state import get_selected_gateway, get_selected_week, is_demo_mode, set_selected_gateway, set_selected_week


def render() -> None:
    """Render the Overview & Control Center page."""
    pred_service = PredictionService()
    gw_service = GatewayService(prediction_service=pred_service)

    demo = is_demo_mode()
    scored_weeks = pred_service.get_scored_weeks()

    # Top Control Bar
    st.markdown("## 📡 Fleet Operations Control Center")
    st.caption("Operational Decision Support for LPWAN Gateway Maintenance & Field Dispatch")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Header controls
    col_w, col_status, col_model = st.columns([1.5, 1.5, 2])

    with col_w:
        current_week = get_selected_week()
        if current_week not in scored_weeks and scored_weeks:
            current_week = scored_weeks[0]
            set_selected_week(current_week)

        selected_week = st.selectbox(
            "Select Prediction Week (Monday 00:00 UTC)",
            options=scored_weeks,
            index=scored_weeks.index(current_week) if current_week in scored_weeks else 0,
            help="Official 8-week competition horizon: 2026-02-02 to 2026-03-23.",
        )
        if selected_week != current_week:
            set_selected_week(selected_week)
            st.rerun()

    with col_status:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🟢 System Status: **ONLINE**")

    with col_model:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Selected Production Architecture: **C3 (HistGradientBoosting)**")

    st.markdown("---")

    # 1. Executive KPI Summary Row
    kpis = pred_service.get_kpis_for_week(selected_week)
    render_overview_kpis(kpis)

    st.markdown("---")

    # 2. 3D Operational Fleet View
    st.markdown("### 🌐 Operational Network / Fleet View — Abstract topology, not geographic coordinates.")
    st.caption(
        "Abstract topological layout representing the gateway fleet. "
        "Elevation (Y-axis) is the primary risk encoding. Color is secondary (Blue <0.30, Amber 0.30–0.70, Red ≥0.70). "
        "Top 15 priority dispatches are marked with purple orbital reticles."
    )

    selected_gw = get_selected_gateway()
    nodes = gw_service.get_fleet_nodes_for_week(
        week_str=selected_week,
        demo_mode=demo,
        selected_gateway_id=selected_gw,
    )

    render_three_fleet_view(nodes=nodes, selected_gateway_id=selected_gw, height=520)

    st.markdown("---")

    # 3. Top 15 Priority Dispatches & Synchronized Quick Inspector
    col_table, col_inspector = st.columns([1.6, 1.0])

    with col_table:
        st.markdown(f"### 📋 Prioritized Dispatches: Week `{selected_week}`")
        st.caption("Official 15 prioritized technician visits under the C3 deterministic dispatch policy.")
        week_preds = pred_service.get_predictions_for_week(selected_week)
        render_priority_table(week_preds)

    with col_inspector:
        st.markdown("### 🔍 Asset Inspector")
        # Dropdown to quickly inspect any of the 15 prioritized gateways or type an ID
        dispatched_ids = list(week_preds["gateway_id"])
        chosen_id = st.selectbox(
            "Select Dispatched Asset to Inspect:",
            options=dispatched_ids if dispatched_ids else ["None"],
            index=0 if dispatched_ids else 0,
        )
        if chosen_id != "None" and chosen_id != selected_gw:
            set_selected_gateway(chosen_id)

        current_inspect_id = get_selected_gateway() or (dispatched_ids[0] if dispatched_ids else None)

        if current_inspect_id:
            details = gw_service.get_gateway_details(current_inspect_id, selected_week, demo_mode=demo)
            render_gateway_inspector(details)
        else:
            st.info("Select a gateway to inspect its telemetry and operational history.")


if __name__ == "__main__":
    render()
