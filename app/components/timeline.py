"""Multi-week dispatch schedule and progression timeline component.

Visualizes dispatches across all 8 official competition weeks.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_dispatch_schedule(df_all_preds: pd.DataFrame) -> None:
    """Render a timeline summary of the 8-week dispatch schedule."""
    if df_all_preds.empty:
        st.info("No predictions available to display.")
        return

    st.markdown("### 📅 Official 8-Week Dispatch Schedule")
    st.caption("15 dispatches per week (120 total) across the February – March 2026 competition window.")

    # Gateway appearance counts
    dispatch_counts = df_all_preds["gateway_id"].value_counts().reset_index()
    dispatch_counts.columns = ["gateway_id", "total_dispatches"]

    col1, col2 = st.columns([2, 1])

    with col1:
        # Heatmap or scatter of week vs rank
        fig = px.scatter(
            df_all_preds,
            x="week_start",
            y="rank",
            color="score",
            hover_data=["gateway_id", "reason"],
            title="Official Dispatches: Weekly Priority Distribution",
            labels={"week_start": "Competition Week", "rank": "Dispatch Priority Rank", "score": "Risk Probability"},
            color_continuous_scale="Viridis",
            template="plotly_dark",
        )
        fig.update_yaxes(autorange="reversed")  # Rank 1 at top
        fig.update_layout(
            paper_bgcolor="#1E222D",
            plot_bgcolor="#131722",
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Gateway Dispatch Frequency")
        st.caption("Assets receiving multiple dispatches (respecting 2-week cooldown):")
        multi_dispatches = dispatch_counts[dispatch_counts["total_dispatches"] > 1]
        st.dataframe(
            multi_dispatches,
            use_container_width=True,
            hide_index=True,
            column_config={
                "gateway_id": "Gateway ID",
                "total_dispatches": st.column_config.NumberColumn("Visits Allocated", format="%d visits"),
            },
        )
