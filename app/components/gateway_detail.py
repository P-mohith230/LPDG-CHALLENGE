"""Detailed operational inspector panel for a single selected gateway.

Respects anti-hallucination policy:
- Real values from predictions.csv and gateway_master.csv.
- If data is unavailable, displays 'Data unavailable from workspace'.
"""

from __future__ import annotations

from typing import Any
import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.formatting import format_percent, format_probability, get_risk_badge


def render_gateway_inspector(details: dict[str, Any]) -> None:
    """Render the operational deep dive card for a single selected gateway."""
    gw_id = details.get("gateway_id", "Unknown")
    meta = details.get("metadata", {})
    pred = details.get("prediction")
    history_df = details.get("history")
    is_synth = details.get("is_synthetic", False)

    st.markdown(f"### 🔍 Gateway Operational Inspector: `{gw_id}`")

    if is_synth:
        st.warning("⚠️ Synthetic demo data active for this gateway — Not official challenge data.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if pred:
            score = pred.get("score")
            st.metric("Predicted Risk Probability", format_probability(score))
            badge_text, badge_color = get_risk_badge(score)
            st.markdown(f"**Status Tier**: <span style='color:{badge_color}; font-weight:bold;'>{badge_text}</span>", unsafe_allow_html=True)
        else:
            st.metric("Predicted Risk Probability", "Not Prioritized")
            st.markdown("**Status Tier**: <span style='color:#3B82F6;'>Within Normal Fleet Range</span>", unsafe_allow_html=True)

    with col2:
        if pred:
            rank = pred.get("rank")
            st.metric("Weekly Dispatch Priority", f"Rank #{rank}" if rank else "None")
        else:
            st.metric("Weekly Dispatch Priority", "Unassigned (>15)")

        antenna = meta.get("antenna_type") or "Data unavailable from workspace"
        st.write(f"**Antenna Hardware**: `{antenna}`")

    with col3:
        meters = meta.get("n_meters_installed") if meta.get("n_meters_installed") is not None else meta.get("meter_count")
        try:
            meter_str = f"{int(meters):,} meters" if meters is not None and pd.notna(meters) else "Data unavailable from workspace"
        except (ValueError, TypeError):
            meter_str = "Data unavailable from workspace"
        st.metric("Associated Smart Meters", meter_str)
        site = meta.get("site_type") or meta.get("site") or "Data unavailable from workspace"
        st.write(f"**Site Deployment**: `{site}`")

    # Diagnostic Explanation
    st.markdown("#### Diagnostic Attribution & Operational Signatures")
    if pred and pred.get("reason"):
        st.info(f"**Documented Dispatch Reason**: {pred['reason']}")
    else:
        st.write("No diagnostic failure alerts triggered for this asset in the selected week.")

    # Historical Telemetry / Read Ratio Trend
    st.markdown("#### Historical Telemetry & Performance Trend")
    if history_df is not None and not history_df.empty:
        # Plot read_ratio over time if available
        if "read_ratio" in history_df.columns:
            fig = px.line(
                history_df,
                x="week_start",
                y="read_ratio",
                markers=True,
                title=f"Historical Collection Read Ratio: `{gw_id}`",
                labels={"read_ratio": "Collection Read Ratio (Meters Read / Expected)", "week_start": "Week Start"},
                template="plotly_dark",
            )
            fig.add_hline(y=0.50, line_dash="dot", line_color="#EF4444", annotation_text="Deficit Threshold (<0.50)")
            fig.update_layout(
                paper_bgcolor="#1E222D",
                plot_bgcolor="#131722",
                yaxis_range=[0.0, 1.05],
                margin=dict(l=30, r=30, t=40, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(history_df.head(10), use_container_width=True)
    else:
        st.caption("Historical meter reading records unavailable for this specific gateway.")
