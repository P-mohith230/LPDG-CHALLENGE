"""Economic Decision Policy, Cooldown Optimization & Ranking Engine.

Source Authority:
- Section 26 [DECISION POLICY GRAPH]:
  Raw model score -> Eligible Gateways -> Cooldown Policy -> Deterministic Sort -> Top 15.
- Section 27 [REVISIT / COOLDOWN LOOP]:
  Evaluate cooldown windows (0, 1, 2, 3 weeks) under official episode simulator.
- Section 29 [DETERMINISTIC RANKING]:
  Enforce strict deterministic sort key: (-risk_score, gateway_id).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd

from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)


@dataclass
class CooldownEvaluationResult:
    """Result of evaluating a cooldown policy over historical weeks."""

    cooldown_weeks: int
    total_cost_eur: float
    visit_cost_eur: float
    penalty_cost_eur: float
    precision_at_15: float
    recall_on_faults: float
    repeat_visits_count: int
    wasted_visits_count: int
    intercepted_faults: int
    unaddressed_faults: int


def rank_gateways_for_week(
    candidates_df: pd.DataFrame,
    visited_history: dict[str, int],
    cooldown_weeks: int = 1,
    visits_per_week: int = 15,
    score_col: str = "risk_score",
    gateway_col: str = "gateway_id",
) -> pd.DataFrame:
    """Select Top 15 gateways for a single decision week applying cooldown and deterministic sorting.

    Args:
        candidates_df: DataFrame containing candidate gateways and risk scores.
        visited_history: Dict mapping gateway_id to weeks elapsed since last visited.
        cooldown_weeks: Number of weeks to suppress repeat dispatches (0 = no cooldown).
        visits_per_week: Number of gateways to select (default: 15).
        score_col: Column name containing predicted failure probability.
        gateway_col: Column name for normalized gateway ID.

    Returns:
        pd.DataFrame containing top ranked gateways with columns [rank, gateway_id, score].
    """
    df = candidates_df.copy()
    df[gateway_col] = normalize_series(df[gateway_col], target_format="bare")

    # Filter out gateways currently in cooldown lockout
    if cooldown_weeks > 0:
        in_cooldown = set()
        for gw, elapsed in visited_history.items():
            if elapsed < cooldown_weeks:
                in_cooldown.add(gw)
        
        eligible_df = df[~df[gateway_col].isin(in_cooldown)].copy()
        # Fallback if eligible candidates are fewer than visits_per_week
        if len(eligible_df) < visits_per_week:
            logger.warning(
                "Cooldown lockout left only %d eligible gateways; relaxing cooldown to fill 15 slots",
                len(eligible_df),
            )
            eligible_df = df.copy()
    else:
        eligible_df = df.copy()

    # Deterministic Sort: Primary = -risk_score (descending), Secondary = gateway_id (ascending)
    sorted_df = eligible_df.sort_values(
        [score_col, gateway_col],
        ascending=[False, True],
    ).reset_index(drop=True)

    selected = sorted_df.head(visits_per_week).copy()
    selected["rank"] = np.arange(1, len(selected) + 1)
    return selected[[gateway_col, score_col, "rank"]]


def simulate_policy_with_cooldown(
    predictions_by_week: dict[pd.Timestamp, pd.DataFrame],
    ground_truth_df: pd.DataFrame,
    cooldown_weeks: int = 1,
    target_col: str = "target_severe_deficit",
    visits_per_week: int = 15,
    cost_per_visit: float = 380.0,
    cost_per_unvisited_fault: float = 600.0,
) -> tuple[pd.DataFrame, CooldownEvaluationResult]:
    """Simulate end-to-end multi-week dispatch policy with dynamic stateful cooldown tracking.

    Args:
        predictions_by_week: Mapping from decision_week to DataFrame containing [gateway_id, risk_score].
        ground_truth_df: Full historical ground truth DataFrame.
        cooldown_weeks: Cooldown lockout duration in weeks.
        target_col: Target column name.
        visits_per_week: Slots per week (default: 15).

    Returns:
        (dispatch_dataframe, evaluation_result)
    """
    from src.evaluation.cost_simulator import simulate_operational_cost

    sorted_mondays = sorted(predictions_by_week.keys())
    visited_history: dict[str, int] = {}
    all_dispatches: list[dict[str, Any]] = []

    for monday in sorted_mondays:
        cand_df = predictions_by_week[monday]
        selected = rank_gateways_for_week(
            candidates_df=cand_df,
            visited_history=visited_history,
            cooldown_weeks=cooldown_weeks,
            visits_per_week=visits_per_week,
        )

        for _, row in selected.iterrows():
            gw = row["gateway_id"]
            all_dispatches.append({
                "week_start": monday,
                "rank": int(row["rank"]),
                "gateway_id": gw,
                "score": float(row["risk_score"]),
                "reason": f"Top-risk candidate (score: {row['risk_score']:.3f})",
            })
            # Reset cooldown timer for this gateway
            visited_history[gw] = 0

        # Increment elapsed weeks for all previously visited gateways
        for gw in list(visited_history.keys()):
            if gw not in selected["gateway_id"].values:
                visited_history[gw] += 1

    disp_df = pd.DataFrame(all_dispatches)

    # Align ground truth week_start
    gt_df = ground_truth_df.copy()
    if "target_week" in gt_df.columns and "week_start" not in gt_df.columns:
        gt_df["week_start"] = gt_df["target_week"]

    cost_res = simulate_operational_cost(
        dispatch_df=disp_df,
        ground_truth_df=gt_df,
        target_col=target_col,
        cost_per_visit=cost_per_visit,
        cost_per_unvisited_fault_week=cost_per_unvisited_fault,
    )

    summary = CooldownEvaluationResult(
        cooldown_weeks=cooldown_weeks,
        total_cost_eur=cost_res.total_operational_cost_eur,
        visit_cost_eur=cost_res.visit_cost_eur,
        penalty_cost_eur=cost_res.missed_fault_penalty_eur,
        precision_at_15=cost_res.precision_at_15,
        recall_on_faults=cost_res.recall_on_faults,
        repeat_visits_count=cost_res.repeat_visits_count,
        wasted_visits_count=cost_res.wasted_visits_count,
        intercepted_faults=cost_res.intercepted_fault_weeks,
        unaddressed_faults=cost_res.unaddressed_fault_weeks,
    )

    return disp_df, summary
