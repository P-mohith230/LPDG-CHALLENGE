"""Validation Splitters for Dual-Dimension Evaluation.

Source Authority:
- Section 21 [VALIDATION GRAPH]:
  "Do NOT randomly shuffle gateway-week data for the main temporal evaluation.
   Do NOT allow same gateway contamination in the dedicated unseen-gateway experiment.
   Do NOT assume GroupKFold alone solves temporal leakage.
   Do NOT assume TimeSeriesSplit alone tests unseen gateways.
   These are complementary questions."
"""

from __future__ import annotations

import logging
from typing import Generator
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

logger = logging.getLogger(__name__)


def get_temporal_walk_forward_splits(
    df: pd.DataFrame,
    date_col: str = "decision_week",
) -> Generator[tuple[np.ndarray, np.ndarray, str], None, None]:
    """Generate forward-time walk-forward evaluation splits.

    Split schedule:
    - Fold 1 (Nov 2025 Val): Train Aug 04 - Oct 27, 2025; Val Nov 03 - Nov 24, 2025
    - Fold 2 (Dec 2025 Val): Train Aug 04 - Nov 24, 2025; Val Dec 01 - Dec 29, 2025
    - Fold 3 (Jan 2026 Val): Train Aug 04 - Dec 29, 2025; Val Jan 05 - Jan 26, 2026

    Args:
        df: Feature/Target DataFrame.
        date_col: Column indicating decision boundary timestamp.

    Yields:
        (train_indices, val_indices, fold_description)
    """
    dates = pd.to_datetime(df[date_col])
    
    # Fold definitions by cutoff date
    folds = [
        ("Fold 1 (Val: Nov 2025)", pd.Timestamp("2025-11-01"), pd.Timestamp("2025-12-01")),
        ("Fold 2 (Val: Dec 2025)", pd.Timestamp("2025-12-01"), pd.Timestamp("2026-01-01")),
        ("Fold 3 (Val: Jan 2026)", pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")),
    ]
    
    for fold_name, val_start, val_end in folds:
        train_mask = (dates < val_start).to_numpy()
        val_mask = ((dates >= val_start) & (dates < val_end)).to_numpy()
        
        train_idx = np.where(train_mask)[0]
        val_idx = np.where(val_mask)[0]
        
        if len(train_idx) == 0 or len(val_idx) == 0:
            logger.warning("Skipping split %s: insufficient samples (train=%d, val=%d)", fold_name, len(train_idx), len(val_idx))
            continue
            
        yield train_idx, val_idx, fold_name


def get_gateway_disjoint_splits(
    df: pd.DataFrame,
    gateway_col: str = "gateway_id",
    n_splits: int = 5,
) -> Generator[tuple[np.ndarray, np.ndarray, str], None, None]:
    """Generate strictly gateway-disjoint K-Fold splits.

    Ensures zero gateway overlap between training and validation folds.
    Tests model generalization to completely unseen hardware installations.

    Args:
        df: Feature/Target DataFrame.
        gateway_col: Gateway ID column.
        n_splits: Number of disjoint gateway folds (default: 5).

    Yields:
        (train_indices, val_indices, fold_description)
    """
    gkf = GroupKFold(n_splits=n_splits)
    groups = df[gateway_col].astype(str)
    
    for fold_i, (train_idx, val_idx) in enumerate(gkf.split(df, groups=groups), start=1):
        fold_name = f"Gateway-Disjoint Fold {fold_i}/{n_splits}"
        # Assert zero intersection
        train_gws = set(df.iloc[train_idx][gateway_col])
        val_gws = set(df.iloc[val_idx][gateway_col])
        assert len(train_gws.intersection(val_gws)) == 0, "FATAL: Gateway overlap detected in disjoint split!"
        
        yield train_idx, val_idx, fold_name
