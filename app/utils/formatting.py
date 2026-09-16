"""Consistent data and display formatting utilities for the dashboard.

Never invents or alters data values. Formats numeric inputs cleanly with currency and units.
"""

from __future__ import annotations

from typing import Any
import pandas as pd


def format_currency(value: float | int | None) -> str:
    """Format a monetary figure in EUR with thousand separators."""
    if value is None or pd.isna(value):
        return "Data unavailable from workspace"
    return f"€{value:,.0f}"


def format_percent(value: float | int | None, decimals: int = 1) -> str:
    """Format a ratio/percentage value."""
    if value is None or pd.isna(value):
        return "Data unavailable from workspace"
    return f"{value * 100:.{decimals}f}%"


def format_probability(value: float | int | None, decimals: int = 4) -> str:
    """Format a risk probability [0, 1]."""
    if value is None or pd.isna(value):
        return "Data unavailable from workspace"
    return f"{value:.{decimals}f}"


def format_hours(value: float | int | None, decimals: int = 1) -> str:
    """Format hours with unit."""
    if value is None or pd.isna(value):
        return "Data unavailable from workspace"
    return f"{value:.{decimals}f}h"


def format_integer(value: int | float | None) -> str:
    """Format integer with thousands separator."""
    if value is None or pd.isna(value):
        return "Data unavailable from workspace"
    return f"{int(value):,}"


def get_risk_badge(score: float | None) -> tuple[str, str]:
    """Return risk tier label and hex color grounded in operational bands."""
    if score is None or pd.isna(score):
        return "Unknown", "#64748B"
    if score >= 0.70:
        return "Critical Risk", "#EF4444"
    if score >= 0.50:
        return "Operational Threshold", "#F59E0B"
    if score >= 0.30:
        return "Moderate Risk", "#EAB308"
    return "Low Risk", "#3B82F6"
