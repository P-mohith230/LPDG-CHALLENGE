"""Service for gateway catalog, fleet statuses, and 3D network node projection.

Follows anti-hallucination rules:
- Elevation is the primary risk encoding.
- Color is the secondary risk encoding.
- Positions are abstract topological coordinates (labeled 'Operational Network / Fleet View').
- Never asserts real geographic coordinates.
"""

from __future__ import annotations

import math
from typing import Any
import pandas as pd

from app.data.adapters import load_gateway_catalog, load_gateway_telemetry_history
from app.services.prediction_service import PredictionService
from app.utils.config import COLORS, RISK_BAND_LOW_MAX, RISK_BAND_MED_MAX


class GatewayService:
    """Service managing gateway fleet state and 3D visual coordinates."""

    def __init__(self, prediction_service: PredictionService | None = None):
        self.pred_service = prediction_service or PredictionService()

    def get_catalog(self, demo_mode: bool = False) -> tuple[pd.DataFrame, bool]:
        """Load gateway catalog and return (dataframe, is_synthetic)."""
        return load_gateway_catalog(demo_mode=demo_mode)

    def get_fleet_nodes_for_week(
        self,
        week_str: str,
        demo_mode: bool = False,
        selected_gateway_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate 3D node representation payload for Three.js.
        
        Elevation (Y) is the primary risk encoding.
        Color is the secondary risk encoding.
        """
        catalog_df, is_synthetic = self.get_catalog(demo_mode=demo_mode)
        week_preds = self.pred_service.get_predictions_for_week(week_str)
        preds_by_id = {row["gateway_id"]: row for _, row in week_preds.iterrows()}

        nodes = []
        total_gateways = len(catalog_df)
        if total_gateways == 0:
            return []

        # Arrange nodes in an abstract concentric phyllotaxis / topological spiral
        # to provide an intuitive, balanced industrial IoT network view
        golden_angle = 137.508 * (math.pi / 180.0)
        spread = 22.0

        for idx, row in catalog_df.iterrows():
            gw_id = str(row["gateway_id"])
            pred = preds_by_id.get(gw_id)

            if pred is not None:
                risk = float(pred["score"])
                is_dispatched = True
                rank = int(pred["rank"])
                reason = str(pred["reason"])
                elevation = risk * 14.0
                if risk >= RISK_BAND_MED_MAX:
                    color = COLORS["status_high"]
                elif risk >= RISK_BAND_LOW_MAX:
                    color = COLORS["status_medium"]
                else:
                    color = COLORS["status_low"]
            else:
                is_dispatched = False
                rank = None
                if demo_mode:
                    # Synthetic demonstration score for demo catalog
                    risk = 0.08 + 0.14 * ((idx % 7) / 7.0)
                    elevation = risk * 14.0
                    color = COLORS["status_low"]
                    reason = "Synthetic demo node: operating within normal baseline range."
                else:
                    # REAL WORKSPACE DATA: Never invent a dummy risk probability for undispatched assets.
                    # Undispatched gateways rest directly on the ground reference plane (elevation = 0.0).
                    risk = None
                    elevation = 0.0
                    color = "#475569"  # Muted industrial datum slate
                    reason = "Not prioritized in top 15 dispatches for this week."

            # Topological abstract X and Z coordinates
            r = spread * math.sqrt((idx + 1) / total_gateways)
            theta = idx * golden_angle
            x = r * math.cos(theta)
            z = r * math.sin(theta)

            is_selected = (gw_id == selected_gateway_id)
            meter_val = row.get("n_meters_installed", row.get("meter_count"))

            nodes.append({
                "gateway_id": gw_id,
                "x": round(x, 2),
                "y": round(elevation, 2),
                "z": round(z, 2),
                "risk": round(risk, 4) if risk is not None else None,
                "elevation": round(elevation, 2),
                "color": color,
                "is_dispatched": is_dispatched,
                "rank": rank,
                "reason": reason,
                "is_selected": is_selected,
                "antenna_type": str(row.get("antenna_type", "Data unavailable from workspace")),
                "meter_count": int(meter_val) if pd.notna(meter_val) else None,
                "is_synthetic": is_synthetic,
            })

        return nodes

    def get_gateway_details(
        self,
        gateway_id: str,
        week_str: str,
        demo_mode: bool = False,
    ) -> dict[str, Any]:
        """Fetch comprehensive details for a single selected gateway."""
        catalog_df, is_synthetic = self.get_catalog(demo_mode=demo_mode)
        gw_rows = catalog_df[catalog_df["gateway_id"] == gateway_id]
        meta = gw_rows.iloc[0].to_dict() if not gw_rows.empty else {}

        pred = self.pred_service.get_prediction_for_gateway(week_str, gateway_id)
        history_df, hist_is_synth = load_gateway_telemetry_history(gateway_id, demo_mode=demo_mode)

        return {
            "gateway_id": gateway_id,
            "metadata": meta,
            "prediction": pred,
            "history": history_df,
            "is_synthetic": is_synthetic or hist_is_synth,
        }
