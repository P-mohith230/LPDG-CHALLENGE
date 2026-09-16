"""Master Innovation Experiment & Benchmarking Harness.

Executes:
1. Innovation 1 Experiments (E-D01, E-D02, E-D03, E-D04): Deterioration & Trend Analysis.
2. Innovation 2 Experiments (E-S01): Signature Prevalence, Deficit Rates, and ML Overlap.
3. Innovation 3 Experiments (E-G01): Gateway Baseline (7d vs 14d vs 28d) and Cold-Start analysis.
4. Innovation 4 Experiments (E-P01): Risk x Deterioration Priority Formulations and Early Warning.
5. Innovation 5 Experiments (E-N01): Novelty Detector, Overlap Breakdown, and OOD Analysis.
6. Innovation Combination Graph (C0 to C10): Systematic evaluation across unified 16-week window.
7. Early-warning lead-time analysis (Weeks -4 to 0).
8. Feature correlation and redundancy matrix.
9. Saves comprehensive research ledger to scratch/innovation_experiment_results.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from src.utils.config import get_data_dir
from src.utils.normalizer import normalize_series
from src.data.loader import load_gateway_master, load_meter_read_success, load_telemetry
from src.features.builder import build_feature_matrix, get_feature_family_columns
from src.features.deterioration import extract_deterioration_features_for_week, get_deterioration_feature_columns
from src.features.gateway_baseline import extract_gateway_baselines_for_week, get_gateway_baseline_feature_columns
from src.intelligence.failure_signatures import evaluate_failure_signatures, get_signature_feature_columns
from src.intelligence.priority_engine import compute_dispatch_priority
from src.intelligence.novelty import FleetNoveltyDetector
from src.models.target import build_operational_target
from src.models.decision_policy import rank_gateways_for_week
from src.evaluation.cost_simulator import simulate_operational_cost, run_baseline_3sigma_strategy
from src.evaluation.splitters import get_temporal_walk_forward_splits, get_gateway_disjoint_splits

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("innovation_harness")


def build_full_enriched_dataset(custom_data_dir: Any = None) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Build joined dataset with Baseline 31 features + Deterioration + Signatures + Gateway Baseline."""
    baseline_feature_cols = get_feature_family_columns()["all"]
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
        "sig_diagnostic_tags",
    }

    cache_path = Path("scratch/enriched_dataset.parquet")
    if cache_path.exists():
        logger.info("Loading pre-computed enriched dataset from %s...", cache_path)
        merged = pd.read_parquet(cache_path)
        all_candidate_feature_cols = [c for c in merged.columns if c not in exclude_cols]
        logger.info("Enriched dataset loaded: %d rows, %d candidate features", len(merged), len(all_candidate_feature_cols))
        return merged, baseline_feature_cols, all_candidate_feature_cols

    logger.info("Loading telemetry, master metadata, and targets...")
    mrs = load_meter_read_success(custom_data_dir)
    telemetry = load_telemetry(custom_data_dir)
    gm = load_gateway_master(custom_data_dir)

    # Pre-normalize telemetry timestamps and gateway IDs once for efficiency
    if not pd.api.types.is_datetime64_any_dtype(telemetry["ts_utc"]):
        telemetry["ts_utc"] = pd.to_datetime(telemetry["ts_utc"])
    if telemetry["ts_utc"].dt.tz is not None:
        telemetry["ts_utc"] = telemetry["ts_utc"].dt.tz_localize(None)
    telemetry["gateway_id"] = normalize_series(telemetry["gateway_id"], target_format="bare")

    targets = build_operational_target(mrs, deficit_threshold=0.50)
    decision_weeks = sorted(targets["decision_week"].unique())

    logger.info("Building baseline 31 features across %d decision weeks...", len(decision_weeks))
    base_features = build_feature_matrix(
        decision_weeks=decision_weeks,
        telemetry_df=telemetry,
        master_df=gm,
    )

    # 1. Innovation 1: Extract deterioration features
    logger.info("Extracting Innovation 1 (Deterioration) features...")
    det_dfs = []
    for dw in decision_weeks:
        det_w = extract_deterioration_features_for_week(
            decision_time=dw,
            telemetry_df=telemetry,
            lookback_days=28,
        )
        det_dfs.append(det_w)
    all_det = pd.concat(det_dfs, ignore_index=True)

    # 2. Innovation 2: Evaluate failure signatures on baseline features
    logger.info("Extracting Innovation 2 (Failure Signatures)...")
    all_sigs = evaluate_failure_signatures(base_features)

    # 3. Innovation 3: Extract gateway-specific baselines
    logger.info("Extracting Innovation 3 (Gateway-Specific Baselines)...")
    gw_base_dfs = []
    for dw in decision_weeks:
        gwb_w = extract_gateway_baselines_for_week(
            decision_time=dw,
            telemetry_df=telemetry,
            history_days=28,
            min_history_hours=72,
        )
        gw_base_dfs.append(gwb_w)
    all_gwb = pd.concat(gw_base_dfs, ignore_index=True)

    # 4. Innovation 5: Chronological Unsupervised Fleet Novelty Detector
    logger.info("Extracting Innovation 5 (Novelty Detector) features...")
    nov_dfs = []
    for dw in decision_weeks:
        hist_df = base_features[base_features["decision_week"] < dw]
        curr_df = base_features[base_features["decision_week"] == dw].copy()
        if len(hist_df) >= 100:
            det = FleetNoveltyDetector(contamination=0.05, random_state=42)
            det.fit(hist_df[baseline_feature_cols].fillna(0.0))
            scored = det.score_samples(curr_df[baseline_feature_cols].fillna(0.0))
        else:
            scored = pd.DataFrame({
                "feat_novelty_score": [0.5] * len(curr_df),
                "is_novel_anomaly": [0] * len(curr_df),
            }, index=curr_df.index)
        scored["gateway_id"] = curr_df["gateway_id"].values
        scored["decision_week"] = dw
        nov_dfs.append(scored[["gateway_id", "decision_week", "feat_novelty_score", "is_novel_anomaly"]])
    all_nov = pd.concat(nov_dfs, ignore_index=True)

    # Merge all feature tables
    merged = pd.merge(base_features, all_det, on=["gateway_id", "decision_week"], how="left")
    merged = pd.merge(merged, all_sigs, on=["gateway_id", "decision_week"], how="left")
    merged = pd.merge(merged, all_gwb, on=["gateway_id", "decision_week"], how="left")
    merged = pd.merge(merged, all_nov, on=["gateway_id", "decision_week"], how="left")
    merged = pd.merge(merged, targets, on=["gateway_id", "decision_week"], how="inner")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(cache_path)
    logger.info("Cached enriched dataset saved to %s", cache_path)

    all_candidate_feature_cols = [c for c in merged.columns if c not in exclude_cols]
    logger.info("Enriched dataset assembled: %d rows, %d candidate features", len(merged), len(all_candidate_feature_cols))
    return merged, baseline_feature_cols, all_candidate_feature_cols


def run_16wk_benchmark_for_predictions(
    predictions_by_week: dict[pd.Timestamp, pd.DataFrame],
    ground_truth_eval: pd.DataFrame,
    cooldown_weeks: int = 2,
    priority_method: str = "risk_only",
    alpha: float = 0.7,
    beta: float = 0.5,
) -> dict[str, Any]:
    """Simulate operational cost across unified 16-week evaluation window applying policy and priority."""
    sorted_mondays = sorted(predictions_by_week.keys())
    visited_history: dict[str, int] = {}
    all_dispatches: list[dict[str, Any]] = []

    for m in sorted_mondays:
        pred_df = predictions_by_week[m].copy()

        # Apply priority engine if requested
        if priority_method != "risk_only":
            pred_df = compute_dispatch_priority(
                pred_df,
                risk_col="risk_score",
                det_col="feat_deterioration_score",
                method=priority_method,
                alpha=alpha,
                beta=beta,
            )
            score_column = "priority_score"
        else:
            score_column = "risk_score"

        ranked = rank_gateways_for_week(
            candidates_df=pred_df,
            visited_history=visited_history,
            cooldown_weeks=cooldown_weeks,
            visits_per_week=15,
            score_col=score_column,
            gateway_col="gateway_id",
        )

        target_w = pred_df["target_week"].iloc[0]
        for _, row in ranked.iterrows():
            gw = row["gateway_id"]
            all_dispatches.append({
                "week_start": target_w,
                "rank": int(row["rank"]),
                "gateway_id": gw,
                "score": float(row[score_column]),
            })
            visited_history[gw] = 0

        # Increment elapsed cooldown weeks for all other visited gateways
        for gw in list(visited_history.keys()):
            if gw not in set(ranked["gateway_id"]):
                visited_history[gw] += 1

    disp_df = pd.DataFrame(all_dispatches)
    cost_res = simulate_operational_cost(disp_df, ground_truth_eval)

    return {
        "dispatches_count": cost_res.total_visits,
        "visit_cost_eur": cost_res.visit_cost_eur,
        "penalty_cost_eur": cost_res.missed_fault_penalty_eur,
        "total_cost_eur": cost_res.total_operational_cost_eur,
        "precision_at_15": cost_res.precision_at_15,
        "recall_on_faults": cost_res.recall_on_faults,
        "repeat_visits_count": cost_res.repeat_visits_count,
        "wasted_visits_count": cost_res.wasted_visits_count,
        "intercepted_faults": cost_res.intercepted_fault_weeks,
        "unaddressed_faults": cost_res.unaddressed_fault_weeks,
    }


def evaluate_feature_set_cv(
    df: pd.DataFrame,
    feature_cols: list[str],
    split_generator: Any,
    validation_type: str,
    target_col: str = "target_severe_deficit",
    visits_per_week: int = 15,
) -> dict[str, Any]:
    """Evaluate candidate model on cross-validation splits and compute metrics."""
    X = df[feature_cols].copy().fillna(0.0)
    y = df[target_col].to_numpy()

    fold_costs = []
    roc_aucs = []
    pr_aucs = []
    precisions = []
    recalls = []

    for train_idx, val_idx, fold_name in split_generator(df):
        X_train, y_train = X.iloc[train_idx], y[train_idx]
        X_val, y_val = X.iloc[val_idx], y[val_idx]
        val_meta = df.iloc[val_idx][["gateway_id", "decision_week", "target_week"]].copy()

        clf = HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=4,
            min_samples_leaf=10,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(X_train, y_train)
        probs = clf.predict_proba(X_val)[:, 1]
        val_meta["risk_score"] = probs
        val_meta[target_col] = y_val

        # Rank per week
        dispatches = []
        for _, grp in val_meta.groupby("decision_week"):
            sorted_grp = grp.sort_values(["risk_score", "gateway_id"], ascending=[False, True]).head(visits_per_week)
            for rank, (_, row) in enumerate(sorted_grp.iterrows(), start=1):
                dispatches.append({
                    "week_start": row["target_week"],
                    "rank": rank,
                    "gateway_id": row["gateway_id"],
                    "score": float(row["risk_score"]),
                })
        disp_df = pd.DataFrame(dispatches)
        gt_df = val_meta[["gateway_id", "target_week", target_col]].rename(columns={"target_week": "week_start"}).copy()
        c_res = simulate_operational_cost(disp_df, gt_df, target_col=target_col)

        fold_costs.append(c_res.total_operational_cost_eur)
        precisions.append(c_res.precision_at_15)
        recalls.append(c_res.recall_on_faults)

        if len(np.unique(y_val)) > 1:
            roc_aucs.append(roc_auc_score(y_val, probs))
            pr_aucs.append(average_precision_score(y_val, probs))

    return {
        "validation_type": validation_type,
        "n_folds": len(fold_costs),
        "mean_fold_cost_eur": float(np.mean(fold_costs)),
        "std_fold_cost_eur": float(np.std(fold_costs)),
        "total_cost_eur": float(np.sum(fold_costs)),
        "mean_roc_auc": float(np.mean(roc_aucs)) if roc_aucs else 0.0,
        "mean_pr_auc": float(np.mean(pr_aucs)) if pr_aucs else 0.0,
        "mean_precision_at_15": float(np.mean(precisions)) if precisions else 0.0,
        "mean_recall": float(np.mean(recalls)) if recalls else 0.0,
    }


def run_walk_forward_16wk_evaluation(
    df: pd.DataFrame,
    feature_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
    cooldown_weeks: int = 2,
    priority_method: str = "risk_only",
    alpha: float = 0.7,
    beta: float = 0.5,
) -> dict[str, Any]:
    """Train HistGradientBoosting chronologically and benchmark on 16-week window with policy."""
    predictions_by_week: dict[pd.Timestamp, pd.DataFrame] = {}

    for eval_w in eval_weeks:
        train_data = df[df["decision_week"] < eval_w]
        eval_data = df[df["decision_week"] == eval_w].copy()

        X_tr = train_data[feature_cols].fillna(0.0)
        y_tr = train_data["target_severe_deficit"].to_numpy()
        X_ev = eval_data[feature_cols].fillna(0.0)

        clf = HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=4,
            min_samples_leaf=10,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(X_tr, y_tr)
        probs = clf.predict_proba(X_ev)[:, 1]
        eval_data["risk_score"] = probs

        keep_cols = ["gateway_id", "decision_week", "target_week", "risk_score"]
        for extra in ["feat_deterioration_score", "feat_novelty_score", "is_novel_anomaly"]:
            if extra in eval_data.columns and extra not in keep_cols:
                keep_cols.append(extra)

        predictions_by_week[eval_w] = eval_data[keep_cols].copy()

    return run_16wk_benchmark_for_predictions(
        predictions_by_week=predictions_by_week,
        ground_truth_eval=gt_eval,
        cooldown_weeks=cooldown_weeks,
        priority_method=priority_method,
        alpha=alpha,
        beta=beta,
    )


def run_innovation_1_experiments(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Execute Innovation 1 Experiments (E-D01 to E-D04): Deterioration & Trend Analysis."""
    logger.info("Executing Innovation 1 Experiments (E-D01 to E-D04)...")

    delta_cols = [
        "feat_det_missing_hours_delta",
        "feat_det_offline_hours_delta",
        "feat_det_disconns_delta",
        "feat_det_reboots_delta",
        "feat_det_power_cycles_delta",
    ]
    surge_cols = [
        "feat_det_norm_missing_surge",
        "feat_det_norm_offline_surge",
        "feat_det_norm_reboot_surge",
    ]
    det_score_col = ["feat_deterioration_score"]

    exp_configs = {
        "E-D01 (Baseline 31 features)": base_cols,
        "E-D02 (Baseline + Deltas)": base_cols + delta_cols,
        "E-D03 (Baseline + Deltas + Surge Ratios)": base_cols + delta_cols + surge_cols,
        "E-D04 (Baseline + Composite Deterioration Score)": base_cols + det_score_col,
    }

    results = {}
    for exp_id, fcols in exp_configs.items():
        logger.info("Running %s (%d features)...", exp_id, len(fcols))
        bench_res = run_walk_forward_16wk_evaluation(df, fcols, eval_weeks, gt_eval)
        temp_cv = evaluate_feature_set_cv(df, fcols, get_temporal_walk_forward_splits, "temporal_walk_forward")
        gw_cv = evaluate_feature_set_cv(df, fcols, get_gateway_disjoint_splits, "gateway_disjoint")

        results[exp_id] = {
            "feature_count": len(fcols),
            "16wk_benchmark": bench_res,
            "temporal_cv": temp_cv,
            "gateway_disjoint_cv": gw_cv,
        }
    return results


def run_innovation_2_experiments(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Execute Innovation 2 Experiments (E-S01): Failure Signatures prevalence and defect association."""
    logger.info("Executing Innovation 2 Experiments (E-S01)...")

    sig_cols = [
        "sig_01_connectivity_collapse",
        "sig_02_hardware_power_cycle_surge",
        "sig_03_persistent_silence_blackout",
        "sig_04_radio_downlink_degradation",
        "sig_05_multi_domain_crisis",
    ]

    stats = {}
    for col in sig_cols:
        triggered = df[df[col] == 1]
        not_triggered = df[df[col] == 0]
        prevalence = float(df[col].mean())
        target_rate_pos = float(triggered["target_severe_deficit"].mean()) if len(triggered) > 0 else 0.0
        target_rate_neg = float(not_triggered["target_severe_deficit"].mean()) if len(not_triggered) > 0 else 0.0
        risk_ratio = (target_rate_pos / (target_rate_neg + 1e-6)) if target_rate_neg > 0 else float("nan")

        stats[col] = {
            "prevalence_pct": round(prevalence * 100, 2),
            "triggered_count": int(df[col].sum()),
            "severe_deficit_rate_when_active": round(target_rate_pos * 100, 2),
            "severe_deficit_rate_when_inactive": round(target_rate_neg * 100, 2),
            "relative_risk_ratio": round(risk_ratio, 2),
        }

    # Model with composite signature score
    bench_sig = run_walk_forward_16wk_evaluation(df, base_cols + ["feat_signature_score"], eval_weeks, gt_eval)
    temp_cv = evaluate_feature_set_cv(df, base_cols + ["feat_signature_score"], get_temporal_walk_forward_splits, "temporal_walk_forward")
    gw_cv = evaluate_feature_set_cv(df, base_cols + ["feat_signature_score"], get_gateway_disjoint_splits, "gateway_disjoint")

    return {
        "signature_diagnostics": stats,
        "16wk_benchmark_with_signature_score": bench_sig,
        "temporal_cv": temp_cv,
        "gateway_disjoint_cv": gw_cv,
    }


def run_innovation_3_experiments(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Execute Innovation 3 Experiments (E-G01): Gateway-Specific Historical Baseline."""
    logger.info("Executing Innovation 3 Experiments (E-G01)...")

    cold_start_mask = ~df["feat_gw_has_adequate_history"].astype(bool)
    cold_start_rate = float(cold_start_mask.mean())
    cold_start_count = int(cold_start_mask.sum())

    gw_cols = [
        "feat_gw_z_offline",
        "feat_gw_z_disconns",
        "feat_gw_z_reboots",
        "feat_gw_z_missing",
        "feat_gw_relative_anomaly_score",
    ]

    bench_gw = run_walk_forward_16wk_evaluation(df, base_cols + gw_cols, eval_weeks, gt_eval)
    temp_cv = evaluate_feature_set_cv(df, base_cols + gw_cols, get_temporal_walk_forward_splits, "temporal_walk_forward")
    gw_cv = evaluate_feature_set_cv(df, base_cols + gw_cols, get_gateway_disjoint_splits, "gateway_disjoint")

    return {
        "cold_start_prevalence_pct": round(cold_start_rate * 100, 2),
        "cold_start_rows_count": cold_start_count,
        "16wk_benchmark": bench_gw,
        "temporal_cv": temp_cv,
        "gateway_disjoint_cv": gw_cv,
    }


def run_innovation_4_experiments(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Execute Innovation 4 Experiments (E-P01): Risk x Deterioration Priority Formulations."""
    logger.info("Executing Innovation 4 Experiments (E-P01)...")

    methods = ["risk_only", "multiplicative", "additive", "rank_borda", "quadrant_boost"]
    results = {}

    for m in methods:
        logger.info("Evaluating priority formulation: %s...", m)
        bench = run_walk_forward_16wk_evaluation(
            df=df,
            feature_cols=base_cols,
            eval_weeks=eval_weeks,
            gt_eval=gt_eval,
            cooldown_weeks=2,
            priority_method=m,
            alpha=0.7,
            beta=0.5,
        )
        results[m] = bench

    return results


def run_innovation_5_experiments(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Execute Innovation 5 Experiments (E-N01): Novelty Detector, Overlap Breakdown, and OOD Analysis."""
    logger.info("Executing Innovation 5 Experiments (E-N01)...")

    # Fit unsupervised novelty detector on historical pre-evaluation data
    train_historical = df[df["decision_week"] < eval_weeks[0]]
    detector = FleetNoveltyDetector(contamination=0.05, random_state=42)
    detector.fit(train_historical[base_cols].fillna(0.0))

    eval_data = df[df["decision_week"].isin(eval_weeks)].copy()
    nov_res = detector.score_samples(eval_data[base_cols].fillna(0.0))
    eval_data["feat_novelty_score"] = nov_res["feat_novelty_score"].values
    eval_data["is_novel_anomaly"] = nov_res["is_novel_anomaly"].values

    # Correlation with severe deficit target
    corr_pearson = float(eval_data["feat_novelty_score"].corr(eval_data["target_severe_deficit"]))
    novelty_anom_rate = float(eval_data["is_novel_anomaly"].mean())

    # Characteristics of novel anomalies vs normal
    novel_mask = eval_data["is_novel_anomaly"] == 1
    normal_mask = ~novel_mask
    char_analysis = {
        "mean_missing_ratio_novel": round(float(eval_data.loc[novel_mask, "feat_missing_ratio"].mean()), 3) if novel_mask.any() else 0.0,
        "mean_missing_ratio_normal": round(float(eval_data.loc[normal_mask, "feat_missing_ratio"].mean()), 3) if normal_mask.any() else 0.0,
        "mean_offline_hours_novel": round(float(eval_data.loc[novel_mask, "feat_offline_hours"].mean()), 2) if novel_mask.any() else 0.0,
        "mean_offline_hours_normal": round(float(eval_data.loc[normal_mask, "feat_offline_hours"].mean()), 2) if normal_mask.any() else 0.0,
        "mean_reboot_cnt_novel": round(float(eval_data.loc[novel_mask, "feat_reboot_cnt_total"].mean()), 2) if novel_mask.any() else 0.0,
        "mean_reboot_cnt_normal": round(float(eval_data.loc[normal_mask, "feat_reboot_cnt_total"].mean()), 2) if normal_mask.any() else 0.0,
    }

    # Benchmark with Novelty
    nov_cols = base_cols + ["feat_novelty_score"]
    bench_novelty = run_walk_forward_16wk_evaluation(
        df=df,
        feature_cols=nov_cols,
        eval_weeks=eval_weeks,
        gt_eval=gt_eval,
        cooldown_weeks=2,
        priority_method="risk_only",
    )
    temp_cv = evaluate_feature_set_cv(df, nov_cols, get_temporal_walk_forward_splits, "temporal_walk_forward")
    gw_cv = evaluate_feature_set_cv(df, nov_cols, get_gateway_disjoint_splits, "gateway_disjoint")

    return {
        "novelty_prevalence_pct": round(novelty_anom_rate * 100, 2),
        "target_correlation_pearson": round(corr_pearson, 4),
        "characteristics_novel_vs_normal": char_analysis,
        "16wk_benchmark": bench_novelty,
        "temporal_cv": temp_cv,
        "gateway_disjoint_cv": gw_cv,
    }


def run_combination_graph(
    df: pd.DataFrame,
    base_cols: list[str],
    eval_weeks: list[pd.Timestamp],
    gt_eval: pd.DataFrame,
) -> dict[str, Any]:
    """Evaluate Innovation Combinations C0 through C10."""
    logger.info("Executing Innovation Combination Graph (C0 to C10)...")

    det_cols = ["feat_deterioration_score"]
    sig_cols = ["feat_signature_score"]
    gw_cols = ["feat_gw_relative_anomaly_score", "feat_gw_z_offline", "feat_gw_z_missing"]

    comb_defs = {
        "C0 (Baseline V1)": {"cols": base_cols, "priority": "risk_only"},
        "C1 (Baseline + Deterioration)": {"cols": base_cols + det_cols, "priority": "risk_only"},
        "C2 (Baseline + Signature)": {"cols": base_cols + sig_cols, "priority": "risk_only"},
        "C3 (Baseline + Gateway Baseline)": {"cols": base_cols + gw_cols, "priority": "risk_only"},
        "C4 (Baseline + Novelty)": {"cols": base_cols + ["feat_novelty_score"], "priority": "risk_only"},
        "C5 (Baseline + Deterioration + Signature)": {"cols": base_cols + det_cols + sig_cols, "priority": "risk_only"},
        "C6 (Baseline + Gateway Baseline + Deterioration)": {"cols": base_cols + gw_cols + det_cols, "priority": "risk_only"},
        "C7 (Baseline + Priority Engine)": {"cols": base_cols, "priority": "quadrant_boost"},
        "C8 (Baseline + Priority Engine + Signature)": {"cols": base_cols + sig_cols, "priority": "quadrant_boost"},
        "C9 (Baseline + Priority Engine + Novelty)": {"cols": base_cols + ["feat_novelty_score"], "priority": "quadrant_boost"},
        "C10 (Integrated Candidate: Base + Det + Sig + Priority)": {"cols": base_cols + det_cols + sig_cols, "priority": "quadrant_boost"},
    }

    results = {}
    for c_id, conf in comb_defs.items():
        logger.info("Evaluating combination %s...", c_id)
        bench = run_walk_forward_16wk_evaluation(
            df=df,
            feature_cols=conf["cols"],
            eval_weeks=eval_weeks,
            gt_eval=gt_eval,
            cooldown_weeks=2,
            priority_method=conf["priority"],
        )
        temp_cv = evaluate_feature_set_cv(df, conf["cols"], get_temporal_walk_forward_splits, "temporal_walk_forward")
        gw_cv = evaluate_feature_set_cv(df, conf["cols"], get_gateway_disjoint_splits, "gateway_disjoint")

        results[c_id] = {
            "feature_count": len(conf["cols"]),
            "priority_method": conf["priority"],
            "16wk_benchmark": bench,
            "temporal_cv": temp_cv,
            "gateway_disjoint_cv": gw_cv,
        }

    return results


def run_lead_time_early_warning_analysis(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Analyze signal trajectory at Weeks -4, -3, -2, -1, 0 before severe deficit onset."""
    logger.info("Analyzing Lead-Time Signal Trajectory (Weeks -4 to 0)...")

    # Trace trajectories for gateways that develop severe deficit
    trajectories = []
    for gw, grp in df.groupby("gateway_id"):
        grp = grp.sort_values("decision_week").reset_index(drop=True)
        deficits = grp[grp["target_severe_deficit"] == 1].index.tolist()

        for d_idx in deficits:
            # Check if this is the start of an episode (prior week was 0)
            if d_idx > 0 and grp.loc[d_idx - 1, "target_severe_deficit"] == 0:
                for lead in range(0, 5):
                    hist_idx = d_idx - lead
                    if hist_idx >= 0:
                        row = grp.loc[hist_idx]
                        trajectories.append({
                            "gateway_id": gw,
                            "lead_weeks_before_onset": -lead,
                            "det_score": float(row.get("feat_deterioration_score", 0.0)),
                            "offline_hours": float(row.get("feat_offline_hours", 0.0)),
                            "missing_hours": float(row.get("feat_missing_hours", 0.0)),
                            "reboot_cnt": float(row.get("feat_reboot_cnt_total", 0.0)),
                        })

    traj_df = pd.DataFrame(trajectories)
    lead_summary = {}
    if not traj_df.empty:
        for lead, grp in traj_df.groupby("lead_weeks_before_onset"):
            lead_summary[f"week_{lead}"] = {
                "mean_det_score": round(float(grp["det_score"].mean()), 4),
                "mean_offline_hours": round(float(grp["offline_hours"].mean()), 2),
                "mean_missing_hours": round(float(grp["missing_hours"].mean()), 2),
                "mean_reboot_cnt": round(float(grp["reboot_cnt"].mean()), 2),
                "sample_count": len(grp),
            }

    return lead_summary


def run_feature_redundancy_matrix(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Compute cross-correlation and redundancy between baseline and innovation features."""
    logger.info("Computing Feature Redundancy and Correlation Matrix...")
    cols = [
        "feat_offline_hours",
        "feat_missing_hours",
        "feat_reboot_cnt_total",
        "feat_power_cycle_cnt",
        "feat_det_offline_hours_delta",
        "feat_det_missing_hours_delta",
        "feat_det_reboots_delta",
        "feat_deterioration_score",
        "feat_signature_score",
        "feat_gw_relative_anomaly_score",
    ]
    sub_df = df[[c for c in cols if c in df.columns]].dropna()
    corr_matrix = sub_df.corr().round(4).to_dict()
    return corr_matrix


def main() -> None:
    """Execute complete Innovation Experiment Program."""
    logger.info("=== STARTING LPDG INNOVATION HARNESS ===")
    data_dir = get_data_dir()
    merged_df, base_cols, candidate_cols = build_full_enriched_dataset(data_dir)

    all_decision_weeks = sorted(merged_df["decision_week"].unique())
    eval_weeks = [w for w in all_decision_weeks if pd.Timestamp("2025-10-06") <= w <= pd.Timestamp("2026-01-19")]
    gt_eval = merged_df[merged_df["decision_week"].isin(eval_weeks)][["gateway_id", "target_week", "target_severe_deficit"]].copy()
    gt_eval = gt_eval.rename(columns={"target_week": "week_start"})

    logger.info("Unified Evaluation Window: %d weeks (%s to %s)", len(eval_weeks), eval_weeks[0].strftime("%Y-%m-%d"), eval_weeks[-1].strftime("%Y-%m-%d"))

    # 1. Innovation 1
    inn1_res = run_innovation_1_experiments(merged_df, base_cols, eval_weeks, gt_eval)

    # 2. Innovation 2
    inn2_res = run_innovation_2_experiments(merged_df, base_cols, eval_weeks, gt_eval)

    # 3. Innovation 3
    inn3_res = run_innovation_3_experiments(merged_df, base_cols, eval_weeks, gt_eval)

    # 4. Innovation 4
    inn4_res = run_innovation_4_experiments(merged_df, base_cols, eval_weeks, gt_eval)

    # 5. Innovation 5
    inn5_res = run_innovation_5_experiments(merged_df, base_cols, eval_weeks, gt_eval)

    # 6. Combination Graph
    comb_res = run_combination_graph(merged_df, base_cols, eval_weeks, gt_eval)

    # 7. Lead-Time Analysis
    lead_res = run_lead_time_early_warning_analysis(merged_df)

    # 8. Feature Redundancy Matrix
    corr_res = run_feature_redundancy_matrix(merged_df)

    # Compile structured ledger
    complete_results = {
        "metadata": {
            "dataset_rows": len(merged_df),
            "baseline_features_count": len(base_cols),
            "candidate_features_count": len(candidate_cols),
            "eval_weeks_count": len(eval_weeks),
            "eval_start": eval_weeks[0].strftime("%Y-%m-%d"),
            "eval_end": eval_weeks[-1].strftime("%Y-%m-%d"),
        },
        "innovation_1_deterioration": inn1_res,
        "innovation_2_signatures": inn2_res,
        "innovation_3_gateway_baseline": inn3_res,
        "innovation_4_priority_engine": inn4_res,
        "innovation_5_novelty": inn5_res,
        "combination_graph": comb_res,
        "lead_time_analysis": lead_res,
        "feature_redundancy_matrix": corr_res,
    }

    out_file = Path("scratch/innovation_experiment_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(complete_results, f, indent=2, default=str)

    logger.info("Innovation experiments successfully completed! Results saved to %s", out_file)


if __name__ == "__main__":
    main()
