"""Plotly 2D data-science visualizations for temporal risk trends and distribution.

Enforces zero-dummy-data rules:
- Sourced directly from predictions.csv or verified experiment artifacts.
- Never creates artificial or fabricated points.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_temporal_risk_trends(df_preds: pd.DataFrame, gateway_id: str | None = None) -> None:
    """Render temporal risk trends across the 8 competition weeks."""
    if df_preds.empty:
        st.info("Insufficient workspace data for this visualization.")
        return

    fig = go.Figure()

    if gateway_id:
        # Trace for the specific selected gateway across weeks
        gw_history = df_preds[df_preds["gateway_id"] == gateway_id].sort_values("week_start")
        if not gw_history.empty:
            fig.add_trace(go.Scatter(
                x=gw_history["week_start"],
                y=gw_history["score"],
                mode="lines+markers",
                name=f"Gateway {gateway_id}",
                line=dict(color="#38BDF8", width=3),
                marker=dict(size=8, color="#38BDF8"),
            ))
        else:
            st.info(f"Gateway {gateway_id} has no dispatched records in predictions.csv.")
            return
    else:
        # Fleet average risk across the 8 weeks
        weekly_stats = df_preds.groupby("week_start")["score"].agg(["mean", "min", "max"]).reset_index()
        fig.add_trace(go.Scatter(
            x=weekly_stats["week_start"],
            y=weekly_stats["mean"],
            mode="lines+markers",
            name="Mean Dispatched Risk (Top 15)",
            line=dict(color="#38BDF8", width=3),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=weekly_stats["week_start"],
            y=weekly_stats["max"],
            mode="lines",
            name="Max Dispatched Risk",
            line=dict(color="#EF4444", width=1.5, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=weekly_stats["week_start"],
            y=weekly_stats["min"],
            mode="lines",
            name="Min Dispatched Risk",
            line=dict(color="#3B82F6", width=1.5, dash="dot"),
        ))

    # Reference threshold line (0.50 operational threshold)
    fig.add_hline(
        y=0.50,
        line_dash="dot",
        line_color="#F59E0B",
        annotation_text="Operational Threshold (p=0.50)",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Temporal Risk Trends across Competition Weeks (2026-02-02 to 2026-03-23)",
        xaxis_title="Dispatch Week Boundary (Monday 00:00 UTC)",
        yaxis_title="Predicted Risk Probability",
        yaxis_range=[0.0, 1.05],
        template="plotly_dark",
        paper_bgcolor="#1E222D",
        plot_bgcolor="#131722",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_distribution(df_week: pd.DataFrame) -> None:
    """Render risk score distribution histogram for the active week's dispatches."""
    if df_week.empty:
        st.info("Insufficient workspace data for this visualization.")
        return

    fig = px.histogram(
        df_week,
        x="score",
        nbins=12,
        title="Distribution of Predicted Risk Scores (Top 15 Dispatches)",
        labels={"score": "Predicted Risk Probability"},
        color_discrete_sequence=["#38BDF8"],
        template="plotly_dark",
    )

    fig.update_layout(
        paper_bgcolor="#1E222D",
        plot_bgcolor="#131722",
        xaxis_range=[0.4, 1.0],
        margin=dict(l=40, r=40, t=50, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_configuration_trade_off_chart(df_configs: pd.DataFrame) -> None:
    """Render the 2D Configuration Trade-off Analysis plot across C0–C10.
    
    Plots Total Operational Cost (€) vs Unseen-Gateway Spatial CV PR-AUC.
    """
    if df_configs.empty:
        st.info("Insufficient experiment artifacts for configuration trade-off chart.")
        return

    fig = px.scatter(
        df_configs,
        x="total_cost_eur",
        y="spatial_pr_auc",
        text="config_id",
        color="status",
        color_discrete_map={
            "Selected Production Architecture": "#10B981",  # Green
            "Documented Alternative": "#F59E0B",           # Amber
            "Evaluated": "#64748B",                        # Muted slate
        },
        hover_data=["full_name", "feature_count", "unaddressed_faults", "spatial_fold_std_eur"],
        title="Configuration Trade-off Analysis: 16-Week Historical Benchmark Cost vs Spatial Generalization",
        labels={
            "total_cost_eur": "16-Week Historical Benchmark Total Cost (€)",
            "spatial_pr_auc": "Unseen-Gateway Spatial CV PR-AUC",
            "status": "Pipeline Status",
        },
        template="plotly_dark",
    )

    fig.update_traces(textposition="top center", marker=dict(size=12, line=dict(width=1, color="#FFFFFF")))

    fig.update_layout(
        paper_bgcolor="#1E222D",
        plot_bgcolor="#131722",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)
