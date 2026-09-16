"""Innovation Lab & Configuration Trade-off Analysis page.

Displays the empirical evaluation across the 11 candidate configurations (C0 through C10):
- Sourced directly from scratch/innovation_experiment_results.json.
- Labeled 'Configuration Trade-off Analysis' (no unverified Pareto claims).
- C3 labeled 'Selected Production Architecture'.
- C10 labeled 'Documented Alternative'.
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

from app.components.risk_chart import render_configuration_trade_off_chart
from app.services.model_service import ModelService
from app.utils.formatting import format_currency
from app.utils.state import is_demo_mode


def render() -> None:
    """Render the Innovation Lab page."""
    demo = is_demo_mode()
    st.markdown("## 🧪 Innovation Lab & Configuration Trade-off Analysis")
    st.caption("Empirical evaluation of 11 pipeline configurations (C0 through C10) evaluated under the historical proxy-target protocol.")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Load trade-off dataframe
    df_configs = ModelService.get_configuration_trade_offs()

    if df_configs.empty:
        st.error("Configuration experiment artifacts unavailable from workspace.")
        return

    # Configuration Trade-off 2D Chart
    render_configuration_trade_off_chart(df_configs)

    st.markdown("---")

    # Comparative Data Table
    st.markdown("### 📋 Configuration Trade-off Reconciliation Table")
    st.caption("All figures evaluated on the 16-week historical benchmark (2025-10-06 to 2026-01-19) against proxy targets.")

    table_display = df_configs.copy()
    table_display["Total Cost"] = table_display["total_cost_eur"].apply(format_currency)
    table_display["Fixed Visit Cost"] = table_display["visit_cost_eur"].apply(format_currency)
    table_display["Penalty Cost"] = table_display["penalty_cost_eur"].apply(format_currency)
    table_display["Spatial PR-AUC"] = table_display["spatial_pr_auc"].apply(lambda v: f"{v:.4f}")
    table_display["Spatial Fold Std"] = table_display["spatial_fold_std_eur"].apply(format_currency)

    show_cols = [
        "config_id",
        "status",
        "feature_count",
        "Total Cost",
        "Fixed Visit Cost",
        "Penalty Cost",
        "unaddressed_faults",
        "Spatial PR-AUC",
        "Spatial Fold Std",
    ]

    st.dataframe(
        table_display[show_cols].rename(columns={
            "config_id": "Config",
            "status": "Production Status",
            "feature_count": "Features",
            "unaddressed_faults": "Unaddressed Faults",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # Executive Summary of Decision
    st.markdown("### ⚖️ Architectural Selection Rationale")
    st.markdown(
        """
        - **C3 (Selected Production Architecture)**:
          Achieved the lowest total operational cost (**€115,200**) and highest spatial generalization (**0.7658 PR-AUC**)
          with the lowest fold variance (**€1,489**). It achieves this using a lean 32-feature set (29 baseline + 3 gateway self-baselines).
        - **C10 (Documented Alternative)**:
          Combines all 5 innovations (39 features) achieving €117,600 total cost. While highly competitive, it carries higher fold variance
          (€2,590) and adds 7 additional features without overcoming C3's cost efficiency.
        """
    )


if __name__ == "__main__":
    render()
