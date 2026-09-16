"""Operational Cost Simulator & Evaluation Engine.

Source Authority:
- [CONFIRMED BY LPDG - Brief p. 3, FAQ Round 1 §4.1, FAQ Round 2 §3.6]:
  Visit cost = €380 per dispatch.
  Unvisited fault penalty = €600 per week an active fault persists unaddressed.
  Budget = 15 visits per week across 8 scored weeks (120 total selections).
  Fixed visit component = 120 x €380 = €45,600.
  Multi-week fault episodes: A visit terminates penalty accrual for that episode.
  Repeat visits within the same active episode waste the €380 visit cost.
- [EVALUATION FIREWALL MANDATE]:
  This simulator is strictly restricted to retrospective offline evaluation.
  It is completely isolated from feature extraction, model training, and inference.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import COST_PER_UNVISITED_FAULT_WEEK, COST_PER_VISIT
from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)


@dataclass
class OperationalCostResult:
    """Detailed financial and operational breakdown of a candidate selection policy."""

    total_visits: int
    visit_cost_eur: float
    total_fault_weeks: int
    intercepted_fault_weeks: int
    unaddressed_fault_weeks: int
    missed_fault_penalty_eur: float
    total_operational_cost_eur: float
    precision_at_15: float
    recall_on_faults: float
    unique_gateways_visited: int
    repeat_visits_count: int
    wasted_visits_count: int  # False alarms + unneeded repeats
    episodes_intercepted: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def simulate_operational_cost(
    dispatch_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    cost_per_visit: float = COST_PER_VISIT,
    cost_per_unvisited_fault_week: float = COST_PER_UNVISITED_FAULT_WEEK,
    target_col: str = "target_severe_deficit",
) -> OperationalCostResult:
    """Simulate total operational cost under official LPDG episode accounting.

    Accounting Logic:
    1. Every dispatch row in dispatch_df costs `cost_per_visit` (€380).
    2. Over the evaluation timeline, each gateway's fault history is evaluated week-by-week.
    3. A fault episode is active when target == 1.
    4. If a gateway is visited during an active fault episode:
       - The visit successfully intercepts the episode.
       - The fault penalty accrual stops for that episode.
       - A second visit to the same gateway during the same continuous active episode is counted as a repeat/wasted visit.
    5. For any week where a gateway is faulty and has NOT been addressed by a visit, it accrues `cost_per_unvisited_fault_week` (€600).
    6. Total cost = Total Visit Cost + Total Unaddressed Fault Cost.

    Args:
        dispatch_df: DataFrame of weekly selections (columns: week_start, gateway_id, rank).
        ground_truth_df: DataFrame of true weekly fault states (columns: week_start, gateway_id, {target_col}).
        cost_per_visit: Cost in EUR per technician dispatch (default: 380.0).
        cost_per_unvisited_fault_week: Penalty in EUR per unvisited fault week (default: 600.0).
        target_col: Binary fault indicator column in ground_truth_df.

    Returns:
        OperationalCostResult dataclass with comprehensive metrics.
    """
    disp = dispatch_df.copy()
    gt = ground_truth_df.copy()

    # Normalize IDs to bare hex
    disp["gateway_id"] = normalize_series(disp["gateway_id"], target_format="bare")
    gt["gateway_id"] = normalize_series(gt["gateway_id"], target_format="bare")

    disp["week_start"] = pd.to_datetime(disp["week_start"])
    gt["week_start"] = pd.to_datetime(gt["week_start"])

    # Dispatches indexed by (week_start, gateway_id)
    dispatch_set = set(zip(disp["week_start"], disp["gateway_id"]))

    total_visits = len(disp)
    visit_cost = total_visits * cost_per_visit

    # Sort ground truth chronologically
    gt = gt.sort_values(["gateway_id", "week_start"]).reset_index(drop=True)
    all_weeks = sorted(gt["week_start"].unique())

    # Group ground truth by gateway
    gt_by_gw = {gw: grp.sort_values("week_start").reset_index(drop=True) for gw, grp in gt.groupby("gateway_id")}

    total_fault_weeks = int(gt[target_col].sum())
    unaddressed_fault_weeks = 0
    intercepted_fault_weeks = 0
    episodes_intercepted = 0
    repeat_visits = 0
    wasted_visits = 0
    true_positive_visits = 0

    # Track visits per gateway across the evaluation horizon
    gw_dispatches_by_week = disp.groupby("gateway_id")["week_start"].apply(set).to_dict()

    for gw, gw_gt in gt_by_gw.items():
        visited_weeks_for_gw = gw_dispatches_by_week.get(gw, set())

        in_episode = False
        episode_addressed = False

        for _, row in gw_gt.iterrows():
            w = row["week_start"]
            is_fault = bool(row[target_col] == 1)
            was_visited = (w in visited_weeks_for_gw)

            if is_fault:
                if not in_episode:
                    # New fault episode starts
                    in_episode = True
                    episode_addressed = False

                if was_visited:
                    if not episode_addressed:
                        # First visit to this episode -> successfully intercepts!
                        episode_addressed = True
                        episodes_intercepted += 1
                        intercepted_fault_weeks += 1
                        true_positive_visits += 1
                    else:
                        # Gateway was already addressed in this episode -> repeat visit waste!
                        repeat_visits += 1
                        wasted_visits += 1
                        intercepted_fault_weeks += 1
                else:
                    if episode_addressed:
                        # Already addressed earlier in the episode -> no new penalty
                        intercepted_fault_weeks += 1
                    else:
                        # Unaddressed fault week -> accrues €600 penalty
                        unaddressed_fault_weeks += 1
            else:
                # Gateway is healthy this week
                in_episode = False
                episode_addressed = False
                if was_visited:
                    # Visited a healthy gateway -> false alarm waste!
                    wasted_visits += 1

    missed_fault_cost = unaddressed_fault_weeks * cost_per_unvisited_fault_week
    total_cost = visit_cost + missed_fault_cost

    precision = true_positive_visits / float(total_visits) if total_visits > 0 else 0.0
    recall = (total_fault_weeks - unaddressed_fault_weeks) / float(total_fault_weeks) if total_fault_weeks > 0 else 0.0
    unique_visited = disp["gateway_id"].nunique()

    return OperationalCostResult(
        total_visits=total_visits,
        visit_cost_eur=round(visit_cost, 2),
        total_fault_weeks=total_fault_weeks,
        intercepted_fault_weeks=intercepted_fault_weeks,
        unaddressed_fault_weeks=unaddressed_fault_weeks,
        missed_fault_penalty_eur=round(missed_fault_cost, 2),
        total_operational_cost_eur=round(total_cost, 2),
        precision_at_15=round(precision, 4),
        recall_on_faults=round(recall, 4),
        unique_gateways_visited=unique_visited,
        repeat_visits_count=repeat_visits,
        wasted_visits_count=wasted_visits,
        episodes_intercepted=episodes_intercepted,
    )


def run_baseline_3sigma_strategy(
    telemetry_df: pd.DataFrame,
    scored_mondays: list[pd.Timestamp | str],
    visits_per_week: int = 15,
    sigma: float = 3.0,
    baseline_days: int = 28,
    recent_days: int = 7,
) -> pd.DataFrame:
    """Execute the official 3-sigma baseline strategy over specified evaluation weeks.

    Reproduces the exact algorithm from baseline_3sigma.py:
    1. Takes trailing 28 days of telemetry strictly before Monday.
    2. Computes mean and std of [offline_duration_sec, disconnection_cnt, reboot_cnt] per gateway.
    3. Flags hours in trailing 7 days exceeding mean + 3*std.
    4. Ranks gateways by flagged hour count (top 15).

    Args:
        telemetry_df: Telemetry DataFrame.
        scored_mondays: List of Monday 00:00:00 UTC timestamps.
        visits_per_week: Number of gateways to select per week (default: 15).
        sigma: Standard deviation threshold (default: 3.0).
        baseline_days: Self-history baseline window in days (default: 28).
        recent_days: Detection window in days (default: 7).

    Returns:
        pd.DataFrame matching submission format [week_start, rank, gateway_id, score, reason].
    """
    metrics = ["offline_duration_sec", "disconnection_cnt", "reboot_cnt"]
    t_df = telemetry_df.copy()
    t_df["gateway_id"] = normalize_series(t_df["gateway_id"], target_format="bare")
    t_df["ts"] = pd.to_datetime(t_df["ts_utc"])
    if t_df["ts"].dt.tz is not None:
        t_df["ts"] = t_df["ts"].dt.tz_localize(None)

    rows = []
    for monday in scored_mondays:
        end = pd.to_datetime(monday)
        if end.tzinfo is not None:
            end = end.tz_localize(None)

        window_start = end - pd.Timedelta(days=baseline_days)
        recent_start = end - pd.Timedelta(days=recent_days)

        window = t_df[(t_df["ts"] >= window_start) & (t_df["ts"] < end)]
        if window.empty:
            continue

        # Per-gateway baseline stats
        stats = window.groupby("gateway_id")[metrics].agg(["mean", "std"])
        recent = window[window["ts"] >= recent_start].copy()

        flags = pd.Series(0, index=recent.index, dtype=int)
        worst = pd.Series("", index=recent.index, dtype=object)

        for metric in metrics:
            mean = recent["gateway_id"].map(stats[(metric, "mean")])
            std = recent["gateway_id"].map(stats[(metric, "std")]).replace(0, np.nan)
            exceeded = (recent[metric] - mean) > (sigma * std)
            exceeded = exceeded.fillna(False)
            flags = flags + exceeded.astype(int)
            worst = worst.where(~exceeded | (worst != ""), metric)

        recent["flagged"] = flags
        recent["worst_metric"] = worst

        grouped = recent.groupby("gateway_id").agg(
            flagged_hours=("flagged", "sum"),
            worst_metric=("worst_metric", lambda s: next((v for v in s if v), "no metric over 3 sigma")),
        ).reset_index()

        # Deterministic sort: flagged_hours DESC, gateway_id ASC
        ranked = grouped.sort_values(["flagged_hours", "gateway_id"], ascending=[False, True]).reset_index(drop=True)

        for rank, row in enumerate(ranked.head(visits_per_week).itertuples(index=False), 1):
            rows.append({
                "week_start": end.strftime("%Y-%m-%d"),
                "rank": rank,
                "gateway_id": row.gateway_id,
                "score": float(row.flagged_hours),
                "reason": (
                    f"{row.flagged_hours} hour(s) beyond 3 sigma of 28d baseline in last 7d; "
                    f"worst breach on {row.worst_metric}"
                )[:300],
            })

    return pd.DataFrame(rows)


def run_random_dispatch_strategy(
    eligible_gateways: list[str],
    scored_mondays: list[pd.Timestamp | str],
    visits_per_week: int = 15,
    seed: int = 42,
) -> pd.DataFrame:
    """Execute a uniform random selection strategy to establish the empirical sanity floor.

    Args:
        eligible_gateways: List of valid bare-hex gateway IDs.
        scored_mondays: List of Monday timestamps.
        visits_per_week: 15 per week.
        seed: Random seed for deterministic reproducibility.

    Returns:
        pd.DataFrame formatted for submission.
    """
    rng = np.random.default_rng(seed)
    gw_list = sorted(list(set(normalize_series(pd.Series(eligible_gateways), target_format="bare"))))

    rows = []
    for monday in scored_mondays:
        end = pd.to_datetime(monday)
        selected = rng.choice(gw_list, size=visits_per_week, replace=False)
        for rank, gw in enumerate(selected, 1):
            rows.append({
                "week_start": end.strftime("%Y-%m-%d"),
                "rank": rank,
                "gateway_id": gw,
                "score": float(visits_per_week - rank + 1),
                "reason": f"Random dispatch baseline selection (seed {seed}) for testing",
            })

    return pd.DataFrame(rows)
