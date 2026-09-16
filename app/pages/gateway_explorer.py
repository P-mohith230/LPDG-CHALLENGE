"""Gateway Explorer page.

Provides fleet-wide asset search, filtering, and deep dive inspection into
operational metrics, antenna characteristics, and 2D temporal telemetry trends.
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
from app.components.risk_chart import render_temporal_risk_trends
from app.services.gateway_service import GatewayService
from app.services.prediction_service import PredictionService
from app.utils.formatting import get_risk_badge
from app.utils.state import get_selected_gateway, get_selected_week, is_demo_mode, set_selected_gateway


def render() -> None:
    """Render the Gateway Explorer page."""
    pred_service = PredictionService()
    gw_service = GatewayService(prediction_service=pred_service)

    demo = is_demo_mode()
    selected_week = get_selected_week()

    st.markdown("## 🔍 Fleet Gateway Explorer")
    st.caption("Search, filter, and inspect operational metrics across the gateway fleet.")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Load fleet catalog
    catalog_df, is_synth = gw_service.get_catalog(demo_mode=demo)

    if catalog_df.empty:
        st.error("Gateway catalog unavailable from workspace.")
        return

    # Attach prediction scores for selected week if dispatched
    week_preds = pred_service.get_predictions_for_week(selected_week)
    pred_map = {row["gateway_id"]: row for _, row in week_preds.iterrows()}

    catalog_display = catalog_df.copy()
    catalog_display["score"] = catalog_display["gateway_id"].apply(
        lambda gid: pred_map[gid]["score"] if gid in pred_map else None
    )
    catalog_display["rank"] = catalog_display["gateway_id"].apply(
        lambda gid: pred_map[gid]["rank"] if gid in pred_map else None
    )
    catalog_display["status_tier"] = catalog_display["score"].apply(
        lambda s: get_risk_badge(s)[0] if s is not None else "Normal Fleet Range"
    )

    # Filtering Controls
    fcol1, fcol2, fcol3 = st.columns(3)

    with fcol1:
        search_query = st.text_input("Search Gateway ID:", placeholder="e.g. 06F49BD8F572").strip()

    with fcol2:
        antenna_opts = ["All"] + sorted([str(a) for a in catalog_df["antenna_type"].dropna().unique()]) if "antenna_type" in catalog_df.columns else ["All"]
        selected_antenna = st.selectbox("Filter by Antenna:", options=antenna_opts)

    with fcol3:
        filter_priority = st.selectbox("Dispatch Status:", options=["All", "Top 15 Dispatched Only", "Normal Fleet Only"])

    # Apply filters
    filtered_df = catalog_display.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["gateway_id"].str.contains(search_query, case=False, na=False)]
    if selected_antenna != "All" and "antenna_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["antenna_type"] == selected_antenna]
    if filter_priority == "Top 15 Dispatched Only":
        filtered_df = filtered_df[filtered_df["rank"].notna()]
    elif filter_priority == "Normal Fleet Only":
        filtered_df = filtered_df[filtered_df["rank"].isna()]

    st.markdown(f"**Showing {len(filtered_df)} of {len(catalog_df)} gateways**")

    # Fleet Table
    show_cols = ["gateway_id"]
    if "antenna_type" in filtered_df.columns:
        show_cols.append("antenna_type")
    meter_col = "n_meters_installed" if "n_meters_installed" in filtered_df.columns else ("meter_count" if "meter_count" in filtered_df.columns else None)
    if meter_col:
        show_cols.append(meter_col)
    show_cols.extend(["rank", "score", "status_tier"])

    st.dataframe(
        filtered_df[show_cols].rename(columns={
            "gateway_id": "Gateway ID",
            "antenna_type": "Antenna Type",
            "n_meters_installed": "Meters",
            "meter_count": "Meters",
            "rank": "Priority Rank",
            "score": "Risk Probability",
            "status_tier": "Status Tier",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # Gateway Deep Dive Inspector
    st.markdown("### 🔎 Individual Asset Inspection")
    gateway_options = list(filtered_df["gateway_id"]) if not filtered_df.empty else list(catalog_df["gateway_id"])
    curr_selected = get_selected_gateway() or (gateway_options[0] if gateway_options else None)

    col_select, _ = st.columns([2, 2])
    with col_select:
        inspected_id = st.selectbox(
            "Select Gateway ID for Deep Dive:",
            options=gateway_options,
            index=gateway_options.index(curr_selected) if curr_selected in gateway_options else 0,
        )
        if inspected_id != curr_selected:
            set_selected_gateway(inspected_id)

    if inspected_id:
        details = gw_service.get_gateway_details(inspected_id, selected_week, demo_mode=demo)
        render_gateway_inspector(details)

        # 2D Temporal Risk Trends for this asset across the 8 weeks
        st.markdown("#### 📈 Multi-Week Dispatched Risk Trend")
        all_preds = pred_service.get_all_predictions()
        render_temporal_risk_trends(all_preds, gateway_id=inspected_id)


if __name__ == "__main__":
    render()
