"""Economic visualization panels enforcing strict separation between official challenge and historical benchmark.

Guarantees:
- Official 8-week challenge costs are never confused with 16-week historical proxy benchmarks.
- Clean visual side-by-side comparison cards and cost breakdown bar charts.
"""

from __future__ import annotations

from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import format_currency, format_percent


def render_economic_overview(
    official_params: dict[str, Any],
    benchmark_data: dict[str, Any],
) -> None:
    """Render the dual-horizon economic panels."""

    # =========================================================================
    # SECTION A: OFFICIAL CHALLENGE CONSTRAINTS (8 WEEKS)
    # =========================================================================
    st.markdown("### 🏆 Section A: Official Challenge Parameters (8 Scored Weeks)")
    st.caption("Official competition evaluation horizon: 2026-02-02 to 2026-03-23 across 120 total technician dispatches.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Evaluation Horizon", "8 Scored Weeks", "Feb 02 – Mar 23, 2026")
    with col2:
        st.metric("Weekly Dispatch Quota", "15 Visits / Week", "Exact capacity")
    with col3:
        st.metric("Technician Visit Rate", "€380 / Visit", "Contracted unit rate")
    with col4:
        st.metric("Fixed 8-Week Visit Budget", "€45,600", "120 visits × €380")

    st.markdown(
        "> **Evaluation Target Notice**: Official competition submissions are scored on **hidden ground truth** "
        "via the competition evaluation portal. The official challenge cost does NOT evaluate proxy targets."
    )

    st.markdown("---")

    # =========================================================================
    # SECTION B: HISTORICAL DEVELOPMENT BENCHMARK (16 WEEKS)
    # =========================================================================
    st.markdown("### 📊 Section B: Historical Development Benchmark (16 Weeks)")
    st.caption(
        "Historical development evaluation horizon: 2025-10-06 to 2026-01-19 (240 visits, €91,200 fixed visit component). "
        "Evaluated against historical collection deficit proxy target (read_ratio < 0.50). NOT hidden official challenge ground truth."
    )

    c3 = benchmark_data.get("c3_production", {})
    c0 = benchmark_data.get("c0_baseline_v1", {})
    c10 = benchmark_data.get("c10_alternative", {})
    ts = benchmark_data.get("three_sigma", {})

    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    with bcol1:
        st.metric(
            "Selected Production Arch (C3)",
            format_currency(c3.get("total_cost_eur")),
            f"-29.9% vs 3-Sigma",
            help="Fixed Visit: €91,200 + Unaddressed Penalty: €24,000 (40 unaddressed faults)",
        )
    with bcol2:
        st.metric(
            "Baseline V1 (C0 / Stage 9)",
            format_currency(c0.get("total_cost_eur")),
            help="Fixed Visit: €91,200 + Unaddressed Penalty: €37,200 (62 unaddressed faults)",
        )
    with bcol3:
        st.metric(
            "Documented Alternative (C10)",
            format_currency(c10.get("total_cost_eur")),
            help="Fixed Visit: €91,200 + Unaddressed Penalty: €26,400 (44 unaddressed faults)",
        )
    with bcol4:
        st.metric(
            "3-Sigma Benchmark",
            format_currency(ts.get("total_cost_eur")),
            help="Fixed Visit: €91,200 + Unaddressed Penalty: €73,200 (122 unaddressed faults)",
        )

    # Visual Stacked Cost Comparison Chart
    chart_data = [
        {"Model": "Selected Production (C3)", "Category": "Fixed Visit Cost (€)", "Cost": 91200.0},
        {"Model": "Selected Production (C3)", "Category": "Unaddressed Penalty Cost (€)", "Cost": c3.get("penalty_cost_eur", 24000.0)},
        {"Model": "Documented Alt (C10)", "Category": "Fixed Visit Cost (€)", "Cost": 91200.0},
        {"Model": "Documented Alt (C10)", "Category": "Unaddressed Penalty Cost (€)", "Cost": c10.get("penalty_cost_eur", 26400.0)},
        {"Model": "Baseline V1 (C0)", "Category": "Fixed Visit Cost (€)", "Cost": 91200.0},
        {"Model": "Baseline V1 (C0)", "Category": "Unaddressed Penalty Cost (€)", "Cost": c0.get("penalty_cost_eur", 37200.0)},
        {"Model": "3-Sigma Benchmark", "Category": "Fixed Visit Cost (€)", "Cost": 91200.0},
        {"Model": "3-Sigma Benchmark", "Category": "Unaddressed Penalty Cost (€)", "Cost": ts.get("penalty_cost_eur", 73200.0)},
    ]
    df_chart = pd.DataFrame(chart_data)

    fig = px.bar(
        df_chart,
        x="Model",
        y="Cost",
        color="Category",
        barmode="stack",
        title="16-Week Historical Development Benchmark: Total Operational Cost Breakdown",
        color_discrete_map={
            "Fixed Visit Cost (€)": "#334155",
            "Unaddressed Penalty Cost (€)": "#EF4444",
        },
        template="plotly_dark",
    )

    fig.update_layout(
        paper_bgcolor="#1E222D",
        plot_bgcolor="#131722",
        yaxis_title="Total Operational Cost (EUR)",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, width="stretch")


def render_what_if_sandbox(sim_result: dict[str, Any]) -> None:
    """Render the isolated What-If simulation results."""
    st.markdown("### 🔬 Technician Capacity Exploration Sandbox")
    st.warning(f"⚠️ **{sim_result.get('disclaimer', 'EXPLORATION ONLY — NOT OFFICIAL SUBMISSION')}**")
    st.caption("Simulates hypothetical operational capacity without altering official predictions.csv.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Simulated Weekly Capacity", f"{sim_result['weekly_capacity']} visits / wk")
    with col2:
        st.metric("Simulated Total Visits", f"{sim_result['total_visits']} visits")
    with col3:
        st.metric("Simulated Visit Cost", format_currency(sim_result["total_visit_cost_eur"]))
    with col4:
        st.metric("Simulated Total Cost", format_currency(sim_result["simulated_total_cost_eur"]))
