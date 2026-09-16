"""Main entry point for the LPDG 2026 Interactive Decision-Support Platform.

Runs via:
    python -m streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit puts the script directory (M:\LPDGE\app) on sys.path.
# We remove it so that "import app..." resolves to the package directory M:\LPDGE\app (not the module app.py).
app_dir = str(Path(__file__).resolve().parent)
project_root = str(Path(__file__).resolve().parent.parent)

sys.path = [p for p in sys.path if p != app_dir]
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from app.pages import (
    economic_analysis,
    gateway_explorer,
    innovation_lab,
    model_intelligence,
    overview,
    system_architecture,
    visit_prioritization,
)
from app.services.prediction_service import PredictionService
from app.utils.config import APP_ICON, APP_SUBTITLE, APP_TITLE, SCORED_WEEKS
from app.utils.state import get_selected_week, init_session_state, is_demo_mode, set_selected_week

# Set Streamlit Page Configuration
st.set_page_config(
    page_title=f"{APP_TITLE} | Operations Control Center",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Industrial Operations Dark Theme CSS
st.markdown(
    """
    <style>
      /* Main container background */
      .stApp {
        background-color: #0E1117;
        color: #F1F5F9;
      }
      /* Sidebar styling */
      [data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid #2A2E39;
      }
      /* Card containers */
      div[data-testid="stMetric"] {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
      }
      /* Clean dataframe borders */
      div[data-testid="stDataFrame"] {
        border: 1px solid #2A2E39;
        border-radius: 8px;
        overflow: hidden;
      }
      /* Top header title */
      h1, h2, h3 {
        color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize application session state
init_session_state()

# Permanent prominent disclosure banner when Demo Mode is active
if is_demo_mode():
    st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**  \n"
               "The platform is operating in isolated synthetic demonstration mode. "
               "Official challenge submission metrics, ranking tables, and predictions remain strictly derived from verified workspace artifacts.")

# Verify Predictions Checksum
pred_service = PredictionService()
checksum_ok, sha256_hash = pred_service.verify_integrity()

# Sidebar Controls
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    st.markdown("---")

    # Scored Week Quick Selector in Sidebar
    st.markdown("### 📅 Active Scored Week")
    scored_weeks = pred_service.get_scored_weeks()
    curr_week = get_selected_week()
    selected_week = st.selectbox(
        "Competition Week:",
        options=scored_weeks,
        index=scored_weeks.index(curr_week) if curr_week in scored_weeks else 0,
        key="sidebar_week_select",
    )
    if selected_week != curr_week:
        set_selected_week(selected_week)
        st.rerun()

    st.markdown("---")

    # Demo Mode Switch
    st.markdown("### 🧪 Operational Mode")
    demo_active = st.toggle("Enable Demo Mode (Synthetic Data)", value=is_demo_mode())
    if demo_active != is_demo_mode():
        st.session_state.demo_mode = demo_active
        st.rerun()

    if demo_active:
        st.warning("⚠️ **DEMO MODE: Synthetic Data — Not Official Challenge Data**\nOfficial predictions.csv remains unaltered.")
    else:
        st.success("🔒 **PRODUCTION MODE**\nConsuming verified workspace artifacts.")

    st.markdown("---")

    # Integrity Status
    st.markdown("### 🛡️ Submission Integrity")
    if checksum_ok:
        st.success("✅ `predictions.csv`: Verified SHA256")
    else:
        st.error(f"❌ Checksum Mismatch:\n`{sha256_hash[:16]}...`")

    st.caption("Selected Production Architecture: **C3** (HistGradientBoosting)")
    st.caption("Version: 1.0.0 (Decoupled Platform)")

# Define native pages using st.navigation
pages = [
    st.Page(overview.render, title="Overview & Control Center", icon="📡", url_path="overview", default=True),
    st.Page(gateway_explorer.render, title="Gateway Explorer", icon="🔍", url_path="gateway-explorer"),
    st.Page(visit_prioritization.render, title="Visit Prioritization", icon="🛠️", url_path="visit-prioritization"),
    st.Page(model_intelligence.render, title="Model Intelligence", icon="🧠", url_path="model-intelligence"),
    st.Page(economic_analysis.render, title="Economic Analysis", icon="💰", url_path="economic-analysis"),
    st.Page(innovation_lab.render, title="Innovation Lab", icon="🧪", url_path="innovation-lab"),
    st.Page(system_architecture.render, title="System Architecture", icon="🏛️", url_path="system-architecture"),
]

nav = st.navigation(pages)
nav.run()
