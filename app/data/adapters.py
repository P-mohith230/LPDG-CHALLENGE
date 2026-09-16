"""Data adapters bridging existing src/ data loaders and artifacts to the dashboard.

Enforces zero-hallucination policy:
- Reads directly from local workspace data when available.
- Catches FileNotFoundError gracefully without inventing placeholder data.
- Explicitly flags whether data is real workspace data or synthetic demo data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import pandas as pd

from app.data.demo_data import generate_synthetic_catalog, generate_synthetic_telemetry_history
from src.utils.config import get_data_dir

logger = logging.getLogger(__name__)


def is_local_challenge_data_available() -> bool:
    """Check if the raw challenge data directory is accessible locally."""
    try:
        data_dir = get_data_dir()
        gm_file = data_dir / "gateway_master.csv"
        return gm_file.is_file()
    except Exception:
        return False


def load_gateway_catalog(demo_mode: bool = False) -> tuple[pd.DataFrame, bool]:
    """Load gateway catalog.
    
    Returns:
        (DataFrame, is_synthetic): tuple containing the gateway dataframe and a boolean
        indicating whether synthetic demo data was loaded.
    """
    if demo_mode:
        return generate_synthetic_catalog(), True

    if is_local_challenge_data_available():
        try:
            from src.data.loader import load_gateway_master
            df = load_gateway_master(normalize_id="bare")
            return df, False
        except Exception as e:
            logger.warning("Failed to load local gateway master: %s", e)

    # In production mode, if local challenge data is missing, fail safely without silent synthetic fallback
    return pd.DataFrame(), False


def load_gateway_telemetry_history(gateway_id: str, demo_mode: bool = False) -> tuple[pd.DataFrame | None, bool]:
    """Load historical meter reading or telemetry summary for a single gateway.
    
    Returns:
        (DataFrame or None, is_synthetic): Dataframe of history, or None if unavailable.
    """
    if demo_mode:
        return generate_synthetic_telemetry_history(gateway_id), True

    if is_local_challenge_data_available():
        try:
            from src.data.loader import load_meter_read_success
            mrs = load_meter_read_success(normalize_id="bare")
            gw_mrs = mrs[mrs["gateway_id"] == gateway_id].copy()
            if not gw_mrs.empty:
                gw_mrs = gw_mrs.sort_values("week_start")
                # Dynamically derive read_ratio from actual meters_read / meters_expected
                if "meters_expected" in gw_mrs.columns and "meters_read" in gw_mrs.columns:
                    expected = gw_mrs["meters_expected"].replace(0, 1)
                    gw_mrs["read_ratio"] = (gw_mrs["meters_read"] / expected).clip(0.0, 1.0)
                return gw_mrs, False
        except Exception as e:
            logger.warning("Failed to load local telemetry history for %s: %s", gateway_id, e)
            return None, False

    return None, False
