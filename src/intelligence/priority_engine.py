"""Innovation 4: Risk × Deterioration Priority Engine.

Source Authority & Method:
- Decouples static predicted operational risk (from ML model) from dynamic failure progression (from Deterioration score).
- Formulates multi-criteria dispatch priority to enable early-warning detection of emerging faults.
- Investigates 4 mathematical formulations:
  1. Additive: P = alpha * Risk + (1 - alpha) * Det
  2. Multiplicative: P = Risk * (1.0 + beta * Det)
  3. Rank-based Borda score: P = gamma * NormalizedRank(Risk) + (1 - gamma) * NormalizedRank(Det)
  4. Quadrant Classification: Categorizes gateways into (High-Risk/High-Det, High-Risk/Low-Det,
     Low-Risk/High-Det [Early Warning], Low-Risk/Low-Det).
- Preserves deterministic sorting: (-priority_score, gateway_id).
"""

from __future__ import annotations

import logging
from typing import Literal
import numpy as np
import pandas as pd

from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)


def compute_dispatch_priority(
    df: pd.DataFrame,
    risk_col: str = "risk_score",
    det_col: str = "feat_deterioration_score",
    method: Literal["additive", "multiplicative", "borda", "risk_only"] = "multiplicative",
    alpha: float = 0.70,
    beta: float = 0.50,
) -> pd.DataFrame:
    """Compute combined operational dispatch priority scores for a decision week.

    Args:
        df: DataFrame containing gateway_id, risk_col, and det_col.
        risk_col: Column containing predicted probability of failure [0.0, 1.0].
        det_col: Column containing deterioration / failure progression score [0.0, 1.0].
        method: Formulation to compute priority score.
        alpha: Weight for risk in additive formulation (default: 0.70).
        beta: Multiplier for deterioration in multiplicative formulation (default: 0.50).

    Returns:
        pd.DataFrame with added columns:
        - priority_score: float in [0.0, 1.0] (or unbounded if ranking)
        - quadrant_class: categorical string (e.g. "Early_Warning_Emerging")
        - priority_rank: deterministic integer rank [1..N]
    """
    out_df = df.copy()
    if "gateway_id" in out_df.columns:
        out_df["gateway_id"] = normalize_series(out_df["gateway_id"], target_format="bare")

    risks = out_df.get(risk_col, pd.Series(0.0, index=out_df.index)).fillna(0.0).astype(float)
    dets = out_df.get(det_col, pd.Series(0.0, index=out_df.index)).fillna(0.0).astype(float)

    if method == "risk_only":
        priority = risks
    elif method == "additive":
        priority = alpha * risks + (1.0 - alpha) * dets
    elif method == "multiplicative":
        # Risk scaled by up to (1 + beta) based on deterioration
        # e.g. beta = 0.5 -> max 1.5x amplification for rapidly deteriorating assets
        priority = risks * (1.0 + beta * dets)
        # Normalize back to [0.0, 1.0] scale
        max_possible = 1.0 * (1.0 + beta)
        priority = priority / max_possible
    elif method in ("borda", "rank_borda"):
        # Rank-based percentile combination
        n = len(out_df)
        if n > 1:
            rank_risk = risks.rank(ascending=True) / float(n)
            rank_det = dets.rank(ascending=True) / float(n)
            priority = alpha * rank_risk + (1.0 - alpha) * rank_det
        else:
            priority = risks
    elif method == "quadrant_boost":
        # Multiplicative priority with bonus for critical accelerating and emerging candidates
        quad_boost = np.where((risks >= 0.5) & (dets >= 0.4), 0.20, 0.0) + np.where((risks < 0.5) & (dets >= 0.6), 0.15, 0.0)
        priority = risks * (1.0 + beta * dets) + quad_boost
        max_possible = 1.0 * (1.0 + beta) + 0.20
        priority = priority / max_possible
    else:
        raise ValueError(f"Unknown priority formulation method: {method}")

    out_df["priority_score"] = np.clip(priority, 0.0, 1.0).round(5)

    # Quadrant Classification (Medians or Threshold 0.5)
    # Class 1: High Risk & High Deterioration -> "Critical_Accelerating"
    # Class 2: High Risk & Low Deterioration  -> "Chronic_Persistent"
    # Class 3: Low Risk & High Deterioration  -> "Early_Warning_Emerging"
    # Class 4: Low Risk & Low Deterioration   -> "Stable_Healthy"
    risk_thresh = 0.60
    det_thresh = 0.50

    def assign_quadrant(r: float, d: float) -> str:
        if r >= risk_thresh and d >= det_thresh:
            return "Critical_Accelerating"
        elif r >= risk_thresh and d < det_thresh:
            return "Chronic_Persistent"
        elif r < risk_thresh and d >= det_thresh:
            return "Early_Warning_Emerging"
        else:
            return "Stable_Healthy"

    out_df["quadrant_class"] = [
        assign_quadrant(r, d) for r, d in zip(risks, dets)
    ]

    # Deterministic Rank: (-priority_score, gateway_id)
    out_df = out_df.sort_values(
        ["priority_score", "gateway_id"],
        ascending=[False, True],
    ).reset_index(drop=True)
    out_df["priority_rank"] = np.arange(1, len(out_df) + 1)

    return out_df
