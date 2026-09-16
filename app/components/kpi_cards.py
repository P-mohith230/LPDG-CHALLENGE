"""Metric summary display cards for dashboard pages.

Presents operational KPIs clearly with units, labels, and provenance.
"""

from __future__ import annotations

import streamlit as st
from app.utils.formatting import format_currency, format_percent


def render_overview_kpis(kpis: dict[str, float | int]) -> None:
    """Render the 4 executive control center KPI cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Weekly Visit Capacity",
            value=f"{kpis.get('available_visits', 15)} Visits",
            help="Official challenge constraint: 15 technician visits allocated per week (€5,700/week).",
        )

    with col2:
        st.metric(
            label="Above Operational Threshold",
            value=f"{kpis.get('above_threshold_count', 0)} Gateways",
            help="Gateways with predicted risk probability p >= 0.50 (operational target collection deficit threshold).",
        )

    with col3:
        avg_risk = kpis.get("avg_risk", 0.0)
        st.metric(
            label="Mean Priority Risk (Top 15)",
            value=format_percent(avg_risk, decimals=1),
            help="Average predicted failure probability across the 15 prioritized gateways for this week.",
        )

    with col4:
        budget = kpis.get("weekly_visit_budget", 5700.0)
        st.metric(
            label="Weekly Visit Expenditure",
            value=format_currency(budget),
            help="Contracted visit expenditure for this week (15 visits × €380/visit = €5,700/week). Total 8-week challenge budget: €45,600.",
        )
