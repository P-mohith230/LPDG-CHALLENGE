"""Economic Analysis page.

Enforces strict separation between:
- Official Challenge Parameters (8 scored weeks, €45,600 fixed visit component).
- Historical Development Benchmark (16 historical weeks, 240 visits, €91,200 fixed visit component).
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

from app.components.economic_panel import render_economic_overview
from app.services.economic_service import EconomicService
from app.utils.state import is_demo_mode


def render() -> None:
    """Render the Economic Analysis page."""
    demo = is_demo_mode()

    st.markdown("## 💰 Economic Analysis & Financial Impact")
    st.caption("Financial reconciliation across official challenge constraints and historical development benchmarks.")

    if demo:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**")

    # Fetch official parameters and historical benchmark figures
    official_params = EconomicService.get_official_challenge_parameters()
    benchmark_data = EconomicService.get_historical_benchmark_data()

    # Render Dual-Horizon Panels
    render_economic_overview(official_params, benchmark_data)

    st.markdown("---")

    # Episode Interruption Economics
    st.markdown("### 🔄 Episode Interruption & Repeat-Visit Economics")
    st.markdown(
        """
        In LPWAN field maintenance, severe outages often persist across consecutive weeks until an onsite repair occurs.
        A naive greedy ranking algorithm repeatedly sends technicians to the same hardware fault week after week,
        burning the fixed 15-visit budget while other fleet gateways collapse unaddressed.

        By enforcing a **2-week cooldown suppression window**:
        1. **Wasted technician visits are eliminated**: No asset is revisited while repairs are being physically resolved.
        2. **Fleet coverage is maximized**: Visit capacity is freed to intercept emerging high-impact faults across the remaining 300+ gateways.
        3. **Financial penalty reduction**: On the 16-week historical benchmark, this mechanism cuts unaddressed fault penalties from **€73,200** to **€24,000** (**-67.2% reduction**).
        """
    )


if __name__ == "__main__":
    render()
