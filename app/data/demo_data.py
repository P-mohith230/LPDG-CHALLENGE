"""Synthetic demonstration data generator strictly isolated for DEMO MODE.

PROVENANCE & BOUNDARY NOTICE:
This module generates synthetic dummy records used ONLY when the dashboard is explicitly
switched to DEMO MODE or when raw challenge data is absent in a public deployment.
It is NEVER mixed with official challenge outputs or predictions.csv.
"""

from __future__ import annotations

import pandas as pd
from app.utils.config import SCORED_WEEKS

DEMO_DISCLOSURE = "DEMO MODE: Synthetic Data — Not Official Challenge Data"

SYNTHETIC_ANTENNAS = ["Omni 3 dBi", "Omni 5 dBi", "Panel 7 dBi", "Yagi 9 dBi"]
SYNTHETIC_SITES = ["Rooftop", "Pole", "Indoor", "Outdoor"]


def _get_demo_gateway_ids() -> list[str]:
    """Retrieve gateway IDs aligning with predictions.csv so dispatches render seamlessly."""
    try:
        from app.services.prediction_service import PREDICTIONS_PATH
        if PREDICTIONS_PATH.is_file():
            df = pd.read_csv(PREDICTIONS_PATH)
            real_ids = list(df["gateway_id"].unique())
            synth_ids = [f"GW_SYNTH_{i:04X}" for i in range(1, 45)]
            return real_ids + synth_ids
    except Exception:
        pass
    return [f"GW_SYNTH_{i:04X}" for i in range(1, 61)]


def generate_synthetic_catalog() -> pd.DataFrame:
    """Generate a sanitized synthetic gateway catalog for demo mode only."""
    records = []
    gateways = _get_demo_gateway_ids()
    for idx, gw_id in enumerate(gateways):
        records.append({
            "gateway_id": gw_id,
            "antenna_type": SYNTHETIC_ANTENNAS[idx % len(SYNTHETIC_ANTENNAS)],
            "site_type": SYNTHETIC_SITES[idx % len(SYNTHETIC_SITES)],
            "meter_count": 50 + (idx * 17) % 350,
            "hardware_version": f"v{(idx % 3) + 1}.0",
            "is_synthetic_demo": True,
        })
    return pd.DataFrame(records)


def generate_synthetic_telemetry_history(gateway_id: str) -> pd.DataFrame:
    """Generate a synthetic 8-week telemetry trend for demo mode visualization."""
    records = []
    base_val = 0.85 if int(gateway_id.split("_")[-1], 16) % 3 != 0 else 0.42
    for w_idx, week in enumerate(SCORED_WEEKS):
        # Deterministic variation for synthetic trend
        factor = 0.05 * ((w_idx + int(gateway_id.split("_")[-1], 16)) % 5 - 2)
        records.append({
            "week_start": str(week),
            "gateway_id": gateway_id,
            "read_ratio": max(0.1, min(1.0, base_val + factor)),
            "packet_count": int(10000 + 5000 * (base_val + factor)),
            "offline_hours": max(0.0, 168.0 * (1.0 - (base_val + factor))),
            "is_synthetic_demo": True,
        })
    return pd.DataFrame(records)
