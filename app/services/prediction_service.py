"""Service managing access to the authoritative predictions.csv artifact.

Strict read-only provenance:
- Never writes, modifies, or overwrites predictions.csv.
- Verifies SHA256 integrity against the official benchmark hash.
- Serves weekly dispatches, ranks, scores, and reasons.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import pandas as pd

from app.utils.config import (
    FAULT_COST_WEEKLY_EUR,
    PROJECT_ROOT,
    REQUIRED_SUBMISSION_COLUMNS,
    RISK_THRESHOLD_OPERATIONAL,
    SCORED_WEEKS,
    VISIT_COST_EUR,
    VISITS_PER_WEEK,
)

PREDICTIONS_PATH = PROJECT_ROOT / "predictions.csv"
EXPECTED_SHA256 = "f27120799bd55bde34508299c411f763d54e7766e266ac54c0619307a6d54608"


class PredictionService:
    """Read-only service for official model predictions."""

    def __init__(self, path: Path | str = PREDICTIONS_PATH):
        self.path = Path(path)
        self._df: pd.DataFrame | None = None
        self._sha256: str | None = None

    def verify_integrity(self) -> tuple[bool, str]:
        """Check SHA256 against expected hash."""
        if not self.path.is_file():
            return False, "File not found"
        with open(self.path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        self._sha256 = digest
        return digest == EXPECTED_SHA256, digest

    def get_all_predictions(self) -> pd.DataFrame:
        """Load and cache predictions dataframe."""
        if self._df is None:
            if not self.path.is_file():
                raise FileNotFoundError(f"predictions.csv not found at {self.path}")
            df = pd.read_csv(self.path)
            # Ensure schema compliance
            for col in REQUIRED_SUBMISSION_COLUMNS:
                if col not in df.columns:
                    raise ValueError(f"Missing required column {col} in predictions.csv")
            self._df = df
        return self._df.copy()

    def get_scored_weeks(self) -> list[str]:
        """Get unique scored week strings from predictions."""
        df = self.get_all_predictions()
        return list(df["week_start"].unique())

    def get_predictions_for_week(self, week_str: str) -> pd.DataFrame:
        """Get 15 prioritized gateways for a specific scored week."""
        df = self.get_all_predictions()
        week_df = df[df["week_start"] == week_str].sort_values("rank")
        return week_df.copy()

    def get_prediction_for_gateway(self, week_str: str, gateway_id: str) -> dict | None:
        """Look up single gateway prediction for a specific week."""
        df = self.get_all_predictions()
        match = df[(df["week_start"] == week_str) & (df["gateway_id"] == gateway_id)]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_kpis_for_week(self, week_str: str) -> dict[str, float | int]:
        """Calculate operational KPIs for the selected week."""
        week_df = self.get_predictions_for_week(week_str)
        if week_df.empty:
            return {
                "available_visits": VISITS_PER_WEEK,
                "above_threshold_count": 0,
                "avg_risk": 0.0,
                "weekly_visit_budget": float(VISITS_PER_WEEK * VISIT_COST_EUR),
            }

        above_threshold = (week_df["score"] >= RISK_THRESHOLD_OPERATIONAL).sum()
        avg_risk = week_df["score"].mean()

        return {
            "available_visits": VISITS_PER_WEEK,
            "above_threshold_count": int(above_threshold),
            "avg_risk": float(avg_risk),
            "weekly_visit_budget": float(VISITS_PER_WEEK * VISIT_COST_EUR),
        }
