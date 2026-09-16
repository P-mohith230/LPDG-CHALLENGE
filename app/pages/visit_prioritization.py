"""Visit Prioritization & Operational Dispatch page.

Features:
- Official 15 prioritized dispatches for the selected week.
- 2-week cooldown suppression tracking.
- Isolated What-If simulation sandbox clearly labeled:
  'EXPLORATION ONLY — NOT OFFICIAL SUBMISSION'.
- 8-week multi-week dispatch timeline.
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

from app.components.economic_panel import render_what_if_sandbox
from app.components.gateway_table import render_priority_table
from app.components.timeline import render_dispatch_schedule
from app.services.economic_service import EconomicService
from app.services.prediction_service import PredictionService
from app.utils.state import get_selected_week, is_demo_mode


def render() -> None:
    """Render the Visit Prioritization page."""
    pred_service = PredictionService()
    selected_week = get_selected_week()
    demo = is_demo_mode()

    st.markdown("## 🛠️ Field Technician Visit Prioritization")
    st.caption("Operational maintenance dispatch under official constraints and decision policy.")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Cooldown Status & Dispatch Table
    st.markdown(f"### 📋 Official Dispatches: Week `{selected_week}`")
    st.caption("These are the 15 gateways prioritized by the selected production architecture (C3) decision policy.")

    week_preds = pred_service.get_predictions_for_week(selected_week)
    render_priority_table(week_preds)

    st.markdown("---")

    # 2-Week Cooldown Policy Explanation & Tracking
    st.markdown("### ⏱️ 2-Week Cooldown Policy Enforcement")
    st.info(
        "**Operational Rule**: A gateway visited in week $k-1$ or $k-2$ is suppressed ($x(g, k) = 0$). "
        "This policy eliminates technician visit waste on chronic unresolved outages, allowing physical repairs "
        "to take effect while maximizing fleet-wide fault interception."
    )

    all_preds = pred_service.get_all_predictions()
    render_dispatch_schedule(all_preds)

    st.markdown("---")

    # Isolated What-If Simulation Sandbox
    st.markdown("### 🧪 What-If Dispatch Exploration Sandbox")
    st.markdown(
        "> ⚠️ **EXPLORATION ONLY — NOT OFFICIAL SUBMISSION**  \n"
        "> This simulation sandbox allows operational dispatchers to test hypothetical variations in weekly technician capacity. "
        "> It operates strictly in memory and does **NOT** alter the official `predictions.csv` or submission outputs."
    )

    sim_col1, sim_col2 = st.columns([2, 1])

    with sim_col1:
        sim_capacity = st.slider(
            "Hypothetical Weekly Visit Capacity:",
            min_value=5,
            max_value=30,
            value=15,
            step=1,
            help="Default is official challenge capacity: 15 visits / week.",
        )

    with sim_col2:
        sim_cooldown = st.selectbox(
            "Hypothetical Cooldown Window:",
            options=[1, 2, 3],
            index=1,
            format_func=lambda x: f"{x}-Week Cooldown" + (" (Official C3)" if x == 2 else ""),
        )

    sim_result = EconomicService.simulate_what_if_capacity(
        weekly_capacity=sim_capacity,
        cooldown_weeks=sim_cooldown,
    )

    render_what_if_sandbox(sim_result)


if __name__ == "__main__":
    render()
