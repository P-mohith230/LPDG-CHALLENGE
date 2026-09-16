"""Model Training, Validation & Progression Harness.

Source Authority:
- Section 20 [MODEL GRAPH]:
  Baseline -> Logistic / ElasticNet -> Random Forest -> Gradient Boosting.
- Section 21 [VALIDATION GRAPH]:
  Temporal Walk-Forward splits & Gateway-Disjoint splits.
- Section 23 [METRIC GRAPH]:
  Primary: Operational Cost (€).
  Secondary: Temporal Generalization, Gateway Generalization, Precision@15, Recall.
- Section 25 [SUSPICIOUS PERFORMANCE FIREWALL]:
  Audit for target-derived features or temporal leakage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data.loader import load_gateway_master, load_meter_read_success, load_telemetry
from src.evaluation.cost_simulator import (
    OperationalCostResult,
    simulate_operational_cost,
)
from src.evaluation.splitters import (
    get_gateway_disjoint_splits,
    get_temporal_walk_forward_splits,
)
from src.features.builder import build_feature_matrix
from src.models.target import (
    build_operational_target,
    validate_target_leakage_firewall,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelEvaluationSummary:
    """Summary of cross-validated model performance across temporal or gateway splits."""

    model_name: str
    validation_type: str
    num_folds: int
    mean_total_cost_eur: float
    total_cost_eur: float
    total_visit_cost_eur: float
    total_penalty_cost_eur: float
    mean_precision_at_15: float
    mean_recall_on_faults: float
    mean_roc_auc: float
    mean_pr_auc: float
    fold_details: list[dict[str, Any]]


def build_candidate_models() -> dict[str, BaseEstimator]:
    """Instantiate candidate models following the project model progression graph.

    Candidate 1: Cost-Weighted L2 Logistic Regression (simple, interpretable baseline)
    Candidate 2: Constrained Random Forest (non-linear interactions, low variance)
    Candidate 3: Regularized HistGradientBoosting (gradient boosting with tree regularization)
    """
    return {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=0.1,
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            )),
        ]),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=4,
            min_samples_leaf=10,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=42,
        ),
    }


def prepare_modeling_dataset(
    custom_data_dir: Any = None,
    target_threshold: float = 0.50,
) -> tuple[pd.DataFrame, list[str]]:
    """Build joined feature and target dataset covering all historical evaluation weeks.

    Returns:
        (df_dataset, feature_columns)
    """
    mrs = load_meter_read_success(custom_data_dir)
    telemetry = load_telemetry(custom_data_dir)
    gm = load_gateway_master(custom_data_dir)

    # 1. Build targets
    targets = build_operational_target(mrs, deficit_threshold=target_threshold)
    
    # 2. Build feature matrix for all decision weeks present in targets
    decision_weeks = sorted(targets["decision_week"].unique())
    features = build_feature_matrix(
        decision_weeks=decision_weeks,
        telemetry_df=telemetry,
        master_df=gm,
    )

    # 3. Join strictly on [gateway_id, decision_week]
    df = pd.merge(features, targets, on=["gateway_id", "decision_week"], how="inner")

    # 4. Programmatic Leakage Audit across all decision boundaries
    for dw in decision_weeks:
        feat_dw = features[features["decision_week"] == dw]
        targ_dw = targets[targets["decision_week"] == dw]
        if not feat_dw.empty and not targ_dw.empty:
            validate_target_leakage_firewall(feat_dw, targ_dw, decision_timestamp=dw)

    # Identify numerical feature columns (exclude metadata and targets)
    exclude_cols = {
        "gateway_id",
        "decision_week",
        "target_week",
        "observation_cutoff_utc",
        "installed_on",
        "meters_read",
        "meters_expected",
        "target_meters_read",
        "target_meters_expected",
        "target_read_ratio",
        "target_severe_deficit",
    }
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    return df, feature_cols


def evaluate_model_pipeline(
    model: BaseEstimator,
    df: pd.DataFrame,
    feature_cols: list[str],
    split_generator: Callable[..., Any],
    validation_type: str,
    target_col: str = "target_severe_deficit",
    visits_per_week: int = 15,
) -> ModelEvaluationSummary:
    """Evaluate candidate model on cross-validation splits and compute simulated operational cost."""
    X = df[feature_cols].copy()
    y = df[target_col].to_numpy()
    
    # Fill any remaining feature NaNs with 0
    X = X.fillna(0.0)

    fold_details = []
    total_cost_accum = 0.0
    total_visit_cost_accum = 0.0
    total_penalty_cost_accum = 0.0
    precisions = []
    recalls = []
    roc_aucs = []
    pr_aucs = []

    for train_idx, val_idx, fold_name in split_generator(df):
        X_train, y_train = X.iloc[train_idx], y[train_idx]
        X_val, y_val = X.iloc[val_idx], y[val_idx]
        val_meta = df.iloc[val_idx][["gateway_id", "decision_week", "target_week"]].copy()

        # Fit model clone
        m = clone(model)
        m.fit(X_train, y_train)

        # Predict probability of fault
        if hasattr(m, "predict_proba"):
            probs = m.predict_proba(X_val)[:, 1]
        elif hasattr(m, "decision_function"):
            scores = m.decision_function(X_val)
            probs = 1.0 / (1.0 + np.exp(-scores))
        else:
            probs = m.predict(X_val)

        val_meta["risk_score"] = probs
        val_meta[target_col] = y_val

        # Compute ranking per decision_week (top 15)
        dispatches = []
        for d_week, grp in val_meta.groupby("decision_week"):
            # Deterministic sorting: (-risk_score, gateway_id)
            sorted_grp = grp.sort_values(["risk_score", "gateway_id"], ascending=[False, True]).head(visits_per_week)
            for rank, (_, row) in enumerate(sorted_grp.iterrows(), start=1):
                dispatches.append({
                    "week_start": row["target_week"],
                    "rank": rank,
                    "gateway_id": row["gateway_id"],
                    "score": float(row["risk_score"]),
                    "reason": f"Model risk: {row['risk_score']:.3f}",
                })

        disp_df = pd.DataFrame(dispatches)

        # Ground truth formatted for simulator
        gt_df = val_meta[["gateway_id", "target_week", target_col]].rename(columns={"target_week": "week_start"}).copy()

        # Operational Cost Simulation
        cost_res = simulate_operational_cost(
            dispatch_df=disp_df,
            ground_truth_df=gt_df,
            target_col=target_col,
        )

        # Classical metrics
        if len(np.unique(y_val)) > 1:
            roc = roc_auc_score(y_val, probs)
            pr = average_precision_score(y_val, probs)
        else:
            roc, pr = 0.5, 0.0

        roc_aucs.append(roc)
        pr_aucs.append(pr)
        precisions.append(cost_res.precision_at_15)
        recalls.append(cost_res.recall_on_faults)
        total_cost_accum += cost_res.total_operational_cost_eur
        total_visit_cost_accum += cost_res.visit_cost_eur
        total_penalty_cost_accum += cost_res.missed_fault_penalty_eur

        fold_details.append({
            "fold_name": fold_name,
            "samples": len(val_idx),
            "faults": int(y_val.sum()),
            "total_cost_eur": cost_res.total_operational_cost_eur,
            "visit_cost_eur": cost_res.visit_cost_eur,
            "penalty_eur": cost_res.missed_fault_penalty_eur,
            "precision_at_15": cost_res.precision_at_15,
            "recall_on_faults": cost_res.recall_on_faults,
            "roc_auc": roc,
            "pr_auc": pr,
            "repeat_visits": cost_res.repeat_visits_count,
            "wasted_visits": cost_res.wasted_visits_count,
        })

    k = max(len(fold_details), 1)
    return ModelEvaluationSummary(
        model_name=type(model).__name__ if not isinstance(model, Pipeline) else type(model.steps[-1][1]).__name__,
        validation_type=validation_type,
        num_folds=k,
        mean_total_cost_eur=round(total_cost_accum / k, 2),
        total_cost_eur=round(total_cost_accum, 2),
        total_visit_cost_eur=round(total_visit_cost_accum, 2),
        total_penalty_cost_eur=round(total_penalty_cost_accum, 2),
        mean_precision_at_15=round(float(np.mean(precisions)), 4),
        mean_recall_on_faults=round(float(np.mean(recalls)), 4),
        mean_roc_auc=round(float(np.mean(roc_aucs)), 4),
        mean_pr_auc=round(float(np.mean(pr_aucs)), 4),
        fold_details=fold_details,
    )


def inspect_model_failure_modes(
    model: BaseEstimator,
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "target_severe_deficit",
    visits_per_week: int = 15,
) -> dict[str, Any]:
    """Inspect false positives and false negatives to diagnose feature/target/model shortcomings."""
    X = df[feature_cols].fillna(0.0)
    y = df[target_col].to_numpy()

    # Train on earlier half, test on later half
    cutoff_date = pd.Timestamp("2025-11-15")
    train_mask = (df["decision_week"] < cutoff_date).to_numpy()
    val_mask = (df["decision_week"] >= cutoff_date).to_numpy()

    m = clone(model)
    m.fit(X.iloc[train_mask], y[train_mask])
    probs = m.predict_proba(X.iloc[val_mask])[:, 1]

    val_df = df.iloc[val_mask].copy()
    val_df["risk_score"] = probs

    # Top 15 ranked per week
    top15_rows = []
    for _, grp in val_df.groupby("decision_week"):
        sorted_grp = grp.sort_values(["risk_score", "gateway_id"], ascending=[False, True]).head(visits_per_week)
        top15_rows.append(sorted_grp)

    selected_df = pd.concat(top15_rows, ignore_index=True)

    # False Positives: Top 15 selected but healthy (target == 0)
    fps = selected_df[selected_df[target_col] == 0]

    # False Negatives: True faults (target == 1) that were NOT in Top 15
    selected_keys = set(zip(selected_df["gateway_id"], selected_df["decision_week"]))
    val_df["is_selected"] = [
        (gw, dw) in selected_keys for gw, dw in zip(val_df["gateway_id"], val_df["decision_week"])
    ]
    fns = val_df[(val_df[target_col] == 1) & (~val_df["is_selected"])]

    return {
        "val_total_faults": int(y[val_mask].sum()),
        "val_total_selected": len(selected_df),
        "false_positive_count": len(fps),
        "false_positive_sample": fps[["gateway_id", "decision_week", "risk_score", "feat_tail_silence", "feat_offline_hours", "feat_reboot_cnt_total"]].head(5).to_dict(orient="records"),
        "false_negative_count": len(fns),
        "false_negative_sample": fns[["gateway_id", "decision_week", "risk_score", "feat_tail_silence", "feat_offline_hours", "feat_reboot_cnt_total"]].head(5).to_dict(orient="records"),
    }
