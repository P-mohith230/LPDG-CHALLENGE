"""Formatted gateway table component with risk status badges.

Directly reflects official predictions.csv dispatches without modification.
"""

from __future__ import annotations

from typing import Callable
import pandas as pd
import streamlit as st

from app.utils.formatting import format_percent, get_risk_badge


def render_priority_table(
    df_week: pd.DataFrame,
    on_select_callback: Callable[[str], None] | None = None,
) -> None:
    """Render the official Top 15 prioritized gateways table."""
    if df_week.empty:
        st.info("No dispatch records available for the selected week.")
        return

    # Add display columns
    display_df = df_week.copy()
    display_df["Risk %"] = display_df["score"].apply(lambda s: f"{s*100:.2f}%")
    display_df["Status Tier"] = display_df["score"].apply(lambda s: get_risk_badge(s)[0])

    cols_to_show = ["rank", "gateway_id", "Risk %", "Status Tier", "reason"]
    renamed_cols = {
        "rank": "Rank",
        "gateway_id": "Gateway ID",
        "reason": "Diagnostic Reason",
    }

    formatted_table = display_df[cols_to_show].rename(columns=renamed_cols)

    st.dataframe(
        formatted_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small", format="#%d"),
            "Gateway ID": st.column_config.TextColumn("Gateway ID", width="medium"),
            "Risk %": st.column_config.TextColumn("Risk Probability", width="medium"),
            "Status Tier": st.column_config.TextColumn("Operational Status", width="medium"),
            "Diagnostic Reason": st.column_config.TextColumn("Diagnostic Explanation", width="large"),
        },
    )
