"""Centralized session state initialization and accessor helpers.

Maintains cross-page state synchronization between 3D scene, tables, and detail panels.
"""

from __future__ import annotations

import streamlit as st
from app.utils.config import SCORED_WEEKS


def init_session_state() -> None:
    """Initialize application session state with defaults from official pipeline."""
    if "selected_week" not in st.session_state:
        # Default to first scored week
        st.session_state.selected_week = str(SCORED_WEEKS[0])

    if "selected_gateway_id" not in st.session_state:
        st.session_state.selected_gateway_id = None

    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False


def set_selected_gateway(gateway_id: str | None) -> None:
    """Update selected gateway across all views."""
    st.session_state.selected_gateway_id = gateway_id


def get_selected_gateway() -> str | None:
    """Retrieve currently selected gateway ID."""
    return st.session_state.get("selected_gateway_id")


def set_selected_week(week_str: str) -> None:
    """Update selected week."""
    st.session_state.selected_week = week_str


def get_selected_week() -> str:
    """Retrieve currently selected week string."""
    return st.session_state.get("selected_week", str(SCORED_WEEKS[0]))


def is_demo_mode() -> bool:
    """Check if synthetic demo mode is currently enabled."""
    return bool(st.session_state.get("demo_mode", False))
