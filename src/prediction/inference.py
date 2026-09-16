"""Production Inference & Final Submission Pipeline.

Source Authority:
- Section 32 [STAGE 9 FINAL INTEGRATION GRAPH]:
  Champion Model (HistGradientBoosting)
  -> Final Inference
  -> Economic Policy (2-week cooldown, deterministic ranking)
  -> Top 15 per week
  -> predictions.csv
  -> validate_submission.py (exit code 0)
- Section 33 [FINAL VALIDATION LOOP]:
  Strict verification of exactly 120 rows, 15/week, ranks 1-15, reasons <= 300 chars.
- Section 34 [REPRODUCIBILITY LOOP]:
  Deterministic seeds and secondary sort key guaranteeing identical byte-for-byte output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from src.data.loader import (
    load_engineer_review,
    load_gateway_master,
    load_meter_read_success,
    load_telemetry,
)
from src.features.builder import (
    build_feature_matrix,
    extract_features_for_decision_week,
    get_feature_family_columns,
)
from src.features.deterioration import extract_deterioration_features_for_week
from src.features.gateway_baseline import extract_gateway_baselines_for_week
from src.intelligence.failure_signatures import evaluate_failure_signatures
from src.intelligence.priority_engine import compute_dispatch_priority
from src.models.decision_policy import rank_gateways_for_week
from src.models.target import build_operational_target, validate_target_leakage_firewall
from src.models.trainer import prepare_modeling_dataset
from src.prediction.reason_builder import build_dispatch_reason
from src.utils.config import (
    MAX_REASON_CHARS,
    PROJECT_ROOT,
    REQUIRED_SUBMISSION_COLUMNS,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
)
from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)


def generate_submission(
    output_path: Path | str = PROJECT_ROOT / "predictions.csv",
    custom_data_dir: Any = None,
    cooldown_weeks: int = 2,
    random_state: int = 42,
    pipeline_mode: str = "promoted_candidate",
) -> pd.DataFrame:
    """Execute end-to-end production pipeline to produce official predictions.csv.

    Modes:
    - 'promoted_candidate': Enriched multi-family pipeline with Gateway-Specific Baselines,
      Deterioration Dynamics, Risk x Deterioration Priority Engine, and Diagnostic Signatures.
    - 'baseline_v1': Frozen 31-feature baseline pipeline with pure risk ranking.

    Args:
        output_path: Target CSV destination.
        custom_data_dir: Optional custom raw data directory.
        cooldown_weeks: Cooldown duration in weeks (default: 2 weeks).
        random_state: Random state for model initialization.
        pipeline_mode: 'promoted_candidate' (default) or 'baseline_v1'.

    Returns:
        pd.DataFrame containing exactly 120 rows formatted for validation.
    """
    logger.info("Executing pipeline mode: %s", pipeline_mode)
    logger.info("Step 1/5: Loading datasets and preparing training features...")

    if pipeline_mode in ("promoted_candidate", "c3", "promoted_candidate_c3"):
        # Winning Champion Architecture: C3 (Baseline 29 + 3 Gateway-Specific Baselines)
        # Lowest 16-wk benchmark cost (€115,200), lowest CV costs, highest unseen-gateway PR-AUC (0.7658)
        cache_path = PROJECT_ROOT / "scratch" / "enriched_dataset.parquet"
        if cache_path.exists():
            logger.info("Loading pre-computed enriched training set from %s...", cache_path)
            df_train = pd.read_parquet(cache_path)
        else:
            from src.experiments.innovation_harness import build_full_enriched_dataset
            df_train, _, _ = build_full_enriched_dataset(custom_data_dir=custom_data_dir)

        base_cols = get_feature_family_columns()["all"]
        c3_extra_cols = [
            "feat_gw_relative_anomaly_score",
            "feat_gw_z_offline",
            "feat_gw_z_missing",
        ]
        feature_cols = [c for c in base_cols + c3_extra_cols if c in df_train.columns]
        score_col = "risk_score"
    elif pipeline_mode in ("c10", "promoted_candidate_c10"):
        # Alternative Candidate Architecture: C10 (Base + Det + Sig + Priority Engine)
        cache_path = PROJECT_ROOT / "scratch" / "enriched_dataset.parquet"
        if cache_path.exists():
            logger.info("Loading pre-computed enriched training set from %s...", cache_path)
            df_train = pd.read_parquet(cache_path)
        else:
            from src.experiments.innovation_harness import build_full_enriched_dataset
            df_train, _, _ = build_full_enriched_dataset(custom_data_dir=custom_data_dir)

        base_cols = get_feature_family_columns()["all"]
        c10_extra_cols = ["feat_deterioration_score", "feat_signature_score"]
        feature_cols = [c for c in base_cols + c10_extra_cols if c in df_train.columns]
        score_col = "priority_score"
    else:
        # Frozen Baseline V1: 31 Features, Pure Risk Ranking
        df_train, feature_cols = prepare_modeling_dataset(custom_data_dir=custom_data_dir)
        score_col = "risk_score"

    X_train = df_train[feature_cols].fillna(0.0)
    y_train = df_train["target_severe_deficit"].to_numpy()

    logger.info(
        "Step 2/5: Fitting Champion Model (HistGradientBoosting, n_samples=%d, n_features=%d)...",
        len(X_train),
        len(feature_cols),
    )
    champion_model = HistGradientBoostingClassifier(
        max_iter=100,
        max_depth=4,
        min_samples_leaf=10,
        learning_rate=0.05,
        class_weight="balanced",
        random_state=random_state,
    )
    champion_model.fit(X_train, y_train)

    logger.info("Step 3/5: Loading operational telemetry and metadata for scored weeks...")
    telemetry_df = load_telemetry(custom_data_dir)
    master_df = load_gateway_master(custom_data_dir)
    engineer_review_df = load_engineer_review(custom_data_dir)

    # Pre-normalize telemetry once for fast inference
    t_df = telemetry_df.copy()
    t_df["gateway_id"] = normalize_series(t_df["gateway_id"], target_format="bare")
    t_df["ts_utc"] = pd.to_datetime(t_df["ts_utc"])
    if t_df["ts_utc"].dt.tz is not None:
        t_df["ts_utc"] = t_df["ts_utc"].dt.tz_localize(None)

    m_df = master_df.copy()
    m_df["gateway_id"] = normalize_series(m_df["gateway_id"], target_format="bare")

    logger.info("Step 4/5: Running inference across 8 scored weeks with 2-week cooldown...")
    visited_history: dict[str, int] = {}
    submission_rows: list[dict[str, Any]] = []

    for week_dt in SCORED_WEEKS:
        decision_dt = pd.Timestamp(week_dt)
        logger.info("  Generating dispatches for week: %s", decision_dt.strftime("%Y-%m-%d"))

        # Extract features strictly before Monday 00:00:00 UTC
        feat_df = extract_features_for_decision_week(
            decision_time=decision_dt,
            telemetry_df=t_df,
            master_df=m_df,
            engineer_review_df=engineer_review_df,
            lookback_days=7,
        )

        # Enforce Global Leakage Firewall
        obs_cutoff = feat_df["observation_cutoff_utc"].iloc[0]
        assert obs_cutoff < decision_dt, f"LEAKAGE: observation_cutoff {obs_cutoff} >= decision_time {decision_dt}"

        if pipeline_mode in ("promoted_candidate", "c3", "promoted_candidate_c3", "c10", "promoted_candidate_c10"):
            # Extract gateway historical baselines (28d self-reference)
            gwb_df = extract_gateway_baselines_for_week(
                decision_time=decision_dt,
                telemetry_df=t_df,
                history_days=28,
                min_history_hours=72,
            )
            # Evaluate domain failure signatures & diagnostic tags for interpretability
            sig_df = evaluate_failure_signatures(feat_df)

            # Merge baseline & signature features
            feat_df = pd.merge(
                feat_df,
                gwb_df[["gateway_id", "feat_gw_relative_anomaly_score", "feat_gw_z_offline", "feat_gw_z_missing"]],
                on="gateway_id",
                how="left",
            )
            feat_df = pd.merge(
                feat_df,
                sig_df[["gateway_id", "feat_signature_score", "sig_diagnostic_tags"]],
                on="gateway_id",
                how="left",
            )

            if pipeline_mode in ("c10", "promoted_candidate_c10"):
                det_df = extract_deterioration_features_for_week(
                    decision_time=decision_dt,
                    telemetry_df=t_df,
                    lookback_days=28,
                )
                feat_df = pd.merge(
                    feat_df,
                    det_df[["gateway_id", "feat_deterioration_score"]],
                    on="gateway_id",
                    how="left",
                )

        # Align feature columns exactly with training schema
        for c in feature_cols:
            if c not in feat_df.columns:
                feat_df[c] = 0.0

        X_infer = feat_df[feature_cols].fillna(0.0)

        # Predict failure probability
        probs = champion_model.predict_proba(X_infer)[:, 1]
        feat_df["risk_score"] = probs

        # Apply dispatch ranking
        if pipeline_mode in ("c10", "promoted_candidate_c10"):
            # Decouple risk from deterioration using priority engine
            feat_df = compute_dispatch_priority(
                feat_df,
                risk_col="risk_score",
                det_col="feat_deterioration_score",
                method="quadrant_boost",
            )
            score_col = "priority_score"
        else:
            score_col = "risk_score"

        # Rank Top 15 using economic policy (2-week cooldown + deterministic sorting)
        ranked = rank_gateways_for_week(
            candidates_df=feat_df,
            visited_history=visited_history,
            cooldown_weeks=cooldown_weeks,
            visits_per_week=VISITS_PER_WEEK,
            score_col=score_col,
            gateway_col="gateway_id",
        )

        # Build evidence-grounded reasons and record dispatches
        for _, row in ranked.iterrows():
            gw = row["gateway_id"]
            rank = int(row["rank"])
            score_val = float(row[score_col])

            # Fetch full feature record for reason generator
            full_row = feat_df[feat_df["gateway_id"] == gw].iloc[0]
            reason = build_dispatch_reason(full_row, max_length=MAX_REASON_CHARS)

            submission_rows.append({
                "week_start": decision_dt.strftime("%Y-%m-%d"),
                "rank": rank,
                "gateway_id": gw,
                "score": round(score_val, 4),
                "reason": reason,
            })

            # Update cooldown timer
            visited_history[gw] = 0

        # Increment elapsed weeks for all unselected gateways
        selected_gws = set(ranked["gateway_id"].values)
        for gw in list(visited_history.keys()):
            if gw not in selected_gws:
                visited_history[gw] += 1

    submission_df = pd.DataFrame(submission_rows)
    # Ensure exact column order
    submission_df = submission_df[REQUIRED_SUBMISSION_COLUMNS]

    # Step 5/5: Write output CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    submission_df.to_csv(output_path, index=False)
    logger.info("Step 5/5: Successfully written %d rows to %s", len(submission_df), output_path)

    return submission_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_submission()

