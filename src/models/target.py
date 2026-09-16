"""Operational target definition, label construction, and leakage firewall.

Source Authority:
- [CONFIRMED BY LPDG - Evaluation Protocol & FAQ Round 2 §4.3, §4.5]:
  Official ground truth is hidden and protected by an evaluation firewall.
  Technician dispatches occur weekly on Monday 00:00 UTC for the upcoming 7-day period.
  Field visits (field_visits.csv) are noisy historical operational logs, not ground truth.
- [OBSERVED IN DATA - Stage 4 Empirical Target Analysis]:
  1. Target A (meters_read / meters_expected < 0.50 at week k+1):
     Prevalence = 7.95% (551/6,927 pairs), 106 unique gateways, monthly std = 0.90% (exceptionally stable).
  2. Target B (telemetry silence >= 24h or offline >= 24h at week k+1):
     Prevalence = 32.81%, monthly std = 9.12% (sensitive to network reporting fluctuations).
  3. Target C (strict composite: deficit < 0.50 AND physical/electrical outage):
     Prevalence = 7.91% (548/6,927 pairs), 99.5% overlap with Target A.
  4. Target D (field repair outcome == 'Fehler behoben' at week k+1):
     Prevalence = 1.65% (114/6,927 pairs), severely limited by historical crew budget (15/wk) and 60.7% no-fault noise.
  5. Binary zero-reads (meters_read == 0):
     Prevalence = 0.03% (2/6,927 pairs). Statistically degenerated as a standalone target.
- [CANDIDATE DECISION - Settled in Stage 4]:
  Decision D-01: Needs a visit is defined as severe collection deficit (read_ratio < 0.50).
  Decision D-02: Target is formulated as 1-week leading indicator Y_{g, k+1} = I(read_ratio_{g, k+1} < 0.50).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from src.utils.config import get_data_dir
from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)

DEFAULT_DEFICIT_THRESHOLD = 0.50
DEFAULT_TARGET_NAME = "target_severe_deficit"

CANDIDATE_TARGETS = {
    "target_severe_deficit_50": "Weekly meter read ratio < 0.50 in week k+1 [PRIMARY CHAMPION]",
    "target_severe_deficit_30": "Weekly meter read ratio < 0.30 in week k+1 [EXTREME SEVERITY]",
    "target_severe_deficit_80": "Weekly meter read ratio < 0.80 in week k+1 [BROAD DEFICIT]",
    "target_persistent_deficit": "Weekly meter read ratio < 0.50 in both week k and week k+1 [PERSISTENT]",
    "target_zero_read": "Weekly meters read == 0 in week k+1 [DEGENERATED / REJECTED]",
    "target_field_repair": "Field visit with outcome 'Fehler behoben' requested in week k+1 [NOISY PROXY]",
    "target_telemetry_outage": "Total offline >= 24h or missing >= 24h in week k+1 [CONNECTIVITY OUTAGE]",
    "target_strict_composite": "Meter read deficit < 0.50 AND physical degradation in week k+1 [COMPOSITE]",
}


def build_operational_target(
    mrs_df: pd.DataFrame,
    deficit_threshold: float = DEFAULT_DEFICIT_THRESHOLD,
    target_name: str = DEFAULT_TARGET_NAME,
    horizon_weeks: int = 1,
) -> pd.DataFrame:
    """Construct the forward-looking operational failure target from meter read success records.

    For each gateway g at decision time T = week_start + 7 days, evaluates the collection
    outcome in week k + horizon_weeks:
        Y_{g, k+1} = I(read_ratio_{g, k+horizon_weeks} < deficit_threshold)

    Strict temporal alignment:
    - Feature window: Week k [week_start, week_start + 7d)
    - Decision boundary: Monday 00:00:00 UTC (week_start + 7d)
    - Target window: Week k+1 [week_start + 7d, week_start + 14d)

    Args:
        mrs_df: DataFrame containing meter read success records (gateway_id, week_start, meters_read, meters_expected).
        deficit_threshold: Read ratio threshold below which a gateway is deemed faulty (default: 0.50).
        target_name: Column name for the synthesized binary target.
        horizon_weeks: Number of weeks ahead to evaluate (default: 1 week).

    Returns:
        pd.DataFrame indexed by [gateway_id, decision_week] with columns:
            - gateway_id: 12-char bare hex ID
            - decision_week: Monday 00:00:00 UTC decision boundary (pd.Timestamp)
            - target_week: Monday 00:00:00 UTC of target evaluation week (pd.Timestamp)
            - target_meters_read: Count of meters successfully read in target week
            - target_meters_expected: Count of meters expected to be read in target week
            - target_read_ratio: meters_read / meters_expected in target week
            - {target_name}: Binary integer indicator (1 if read_ratio < deficit_threshold, 0 otherwise)
    """
    df = mrs_df.copy()

    # Ensure clean types and bare hex ID
    df["gateway_id"] = normalize_series(df["gateway_id"], target_format="bare")
    df["week_start"] = pd.to_datetime(df["week_start"])
    if "read_ratio" not in df.columns:
        df["read_ratio"] = df["meters_read"] / df["meters_expected"]

    # Sort strictly by gateway and week
    df = df.sort_values(["gateway_id", "week_start"]).reset_index(drop=True)

    # Lead variables for future week k + horizon_weeks
    grouped = df.groupby("gateway_id")
    df["target_week"] = grouped["week_start"].shift(-horizon_weeks)
    df["target_meters_read"] = grouped["meters_read"].shift(-horizon_weeks)
    df["target_meters_expected"] = grouped["meters_expected"].shift(-horizon_weeks)
    df["target_read_ratio"] = grouped["read_ratio"].shift(-horizon_weeks)

    # The decision week is the exact Monday 00:00 UTC boundary immediately following week k
    df["decision_week"] = df["week_start"] + pd.Timedelta(days=7)

    # Filter strictly to contiguous weeks where target_week == decision_week + (horizon_weeks - 1)*7d
    expected_target_week = df["decision_week"] + pd.Timedelta(days=(horizon_weeks - 1) * 7)
    valid_mask = (df["target_week"] == expected_target_week) & df["target_read_ratio"].notna()
    result = df[valid_mask].copy()

    # Formulate binary failure target
    result[target_name] = (result["target_read_ratio"] < deficit_threshold).astype(int)

    output_cols = [
        "gateway_id",
        "decision_week",
        "target_week",
        "target_meters_read",
        "target_meters_expected",
        "target_read_ratio",
        target_name,
    ]
    return result[output_cols].reset_index(drop=True)


def build_candidate_targets(
    mrs_df: pd.DataFrame,
    field_visits_df: pd.DataFrame | None = None,
    telemetry_weekly_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build all candidate target formulations for comparative empirical evaluation.

    Args:
        mrs_df: DataFrame of meter read success records.
        field_visits_df: Optional DataFrame of historical field visits.
        telemetry_weekly_df: Optional pre-aggregated weekly telemetry metrics (missing_hours, sum_offline_sec, sum_power_cycles).

    Returns:
        pd.DataFrame containing pairs aligned at decision_week with all candidate target columns.
    """
    # Primary Target A variations
    t_50 = build_operational_target(mrs_df, deficit_threshold=0.50, target_name="target_severe_deficit_50")
    t_30 = build_operational_target(mrs_df, deficit_threshold=0.30, target_name="target_severe_deficit_30")
    t_80 = build_operational_target(mrs_df, deficit_threshold=0.80, target_name="target_severe_deficit_80")

    merged = t_50.copy()
    merged["target_severe_deficit_30"] = t_30["target_severe_deficit_30"]
    merged["target_severe_deficit_80"] = t_80["target_severe_deficit_80"]
    merged["target_zero_read"] = (merged["target_meters_read"] == 0).astype(int)

    # Contemporaneous read ratio in week k (before decision_week)
    mrs_clean = mrs_df.copy()
    mrs_clean["gateway_id"] = normalize_series(mrs_clean["gateway_id"], target_format="bare")
    mrs_clean["decision_week"] = pd.to_datetime(mrs_clean["week_start"]) + pd.Timedelta(days=7)
    mrs_clean["current_read_ratio"] = mrs_clean["meters_read"] / mrs_clean["meters_expected"]
    merged = pd.merge(
        merged,
        mrs_clean[["gateway_id", "decision_week", "current_read_ratio"]],
        on=["gateway_id", "decision_week"],
        how="left",
    )
    merged["target_persistent_deficit"] = (
        (merged["current_read_ratio"] < 0.50) & (merged["target_severe_deficit_50"] == 1)
    ).astype(int)

    # Optional Target D: Field visits
    if field_visits_df is not None:
        fv = field_visits_df.copy()
        fv["gateway_id"] = normalize_series(fv["gateway_id"], target_format="bare")
        fv["requested_on"] = pd.to_datetime(fv["requested_on"])
        repairs = fv[fv["outcome"] == "Fehler behoben"].copy()

        repair_flags = []
        for _, row in merged.iterrows():
            gw = row["gateway_id"]
            w_start = row["target_week"]
            w_end = w_start + pd.Timedelta(days=7)
            has_rep = ((repairs["gateway_id"] == gw) & (repairs["requested_on"] >= w_start) & (repairs["requested_on"] < w_end)).any()
            repair_flags.append(int(has_rep))
        merged["target_field_repair"] = repair_flags

    # Optional Target B & C: Telemetry weekly
    if telemetry_weekly_df is not None:
        tw = telemetry_weekly_df.copy()
        tw["gateway_id"] = normalize_series(tw["gateway_id"], target_format="bare")
        tw["target_week"] = pd.to_datetime(tw["week_start"])
        merged = pd.merge(
            merged,
            tw[["gateway_id", "target_week", "missing_hours", "sum_offline_sec", "sum_power_cycles"]],
            on=["gateway_id", "target_week"],
            how="left",
        )
        merged["missing_hours"] = merged["missing_hours"].fillna(0)
        merged["sum_offline_sec"] = merged["sum_offline_sec"].fillna(0)
        merged["sum_power_cycles"] = merged["sum_power_cycles"].fillna(0)

        # B: Telemetry outage (missing >= 24h OR offline >= 24h)
        merged["target_telemetry_outage"] = (
            (merged["missing_hours"] >= 24) | (merged["sum_offline_sec"] >= 24 * 3600)
        ).astype(int)

        # C: Strict composite (meter deficit < 0.50 AND (telemetry outage OR power cycles > 5))
        merged["target_strict_composite"] = (
            (merged["target_severe_deficit_50"] == 1)
            & ((merged["target_telemetry_outage"] == 1) | (merged["sum_power_cycles"] > 5))
        ).astype(int)

    return merged


def validate_target_leakage_firewall(
    features_df: pd.DataFrame,
    targets_df: pd.DataFrame,
    decision_timestamp: pd.Timestamp | str,
    feature_timestamp_col: str = "observation_cutoff_utc",
    target_start_col: str = "target_week",
    forbidden_substrings: list[str] | None = None,
) -> dict[str, Any]:
    """Verify that zero future target information leaks into the feature matrix across decision boundaries.

    Enforces the Global Leakage Firewall:
    - Every feature record must satisfy: timestamp < decision_timestamp.
    - Every target record must satisfy: target_start >= decision_timestamp.
    - No target-derived column names exist in features_df.
    - Index keys (gateway_id, decision_week) match 1-to-1 without duplicates.

    Args:
        features_df: DataFrame containing features computed strictly prior to decision boundary.
        targets_df: DataFrame containing forward-looking targets.
        decision_timestamp: The exact Monday 00:00:00 UTC decision boundary.
        feature_timestamp_col: Column recording the upper time bound of feature observations.
        target_start_col: Column recording the start of the target evaluation window.
        forbidden_substrings: Column name tokens forbidden from appearing in features (e.g. ['target', 'outcome']).

    Returns:
        Dictionary of audit results with boolean 'passed' and detailed checks.

    Raises:
        ValueError: If a leakage violation is detected.
    """
    decision_dt = pd.to_datetime(decision_timestamp)
    if decision_dt.tzinfo is not None:
        decision_dt = decision_dt.tz_localize(None)

    checks: dict[str, Any] = {
        "decision_timestamp": str(decision_dt),
        "feature_count": len(features_df),
        "target_count": len(targets_df),
        "timestamp_firewall_passed": True,
        "column_name_firewall_passed": True,
        "duplicate_key_firewall_passed": True,
        "passed": True,
        "violations": [],
    }

    # 1. Feature timestamp assertion
    if feature_timestamp_col in features_df.columns:
        feat_ts = pd.to_datetime(features_df[feature_timestamp_col])
        if feat_ts.dt.tz is not None:
            feat_ts = feat_ts.dt.tz_localize(None)
        future_mask = feat_ts >= decision_dt
        if future_mask.any():
            violating_cnt = int(future_mask.sum())
            msg = f"LEAKAGE VIOLATION: {violating_cnt} feature rows have {feature_timestamp_col} >= {decision_dt}"
            checks["timestamp_firewall_passed"] = False
            checks["violations"].append(msg)
            checks["passed"] = False
            raise ValueError(msg)

    # 2. Target timestamp assertion
    if target_start_col in targets_df.columns:
        target_ts = pd.to_datetime(targets_df[target_start_col])
        if target_ts.dt.tz is not None:
            target_ts = target_ts.dt.tz_localize(None)
        past_mask = target_ts < decision_dt
        if past_mask.any():
            violating_cnt = int(past_mask.sum())
            msg = f"LEAKAGE VIOLATION: {violating_cnt} target rows have {target_start_col} < {decision_dt}"
            checks["timestamp_firewall_passed"] = False
            checks["violations"].append(msg)
            checks["passed"] = False
            raise ValueError(msg)

    # 3. Column name inspection
    if forbidden_substrings is None:
        forbidden_substrings = ["target_", "outcome", "meters_read_next", "future_"]

    forbidden_found = [
        col for col in features_df.columns
        if any(tok in col.lower() for tok in forbidden_substrings)
    ]
    if forbidden_found:
        msg = f"LEAKAGE VIOLATION: Forbidden target-derived columns detected in features: {forbidden_found}"
        checks["column_name_firewall_passed"] = False
        checks["violations"].append(msg)
        checks["passed"] = False
        raise ValueError(msg)

    # 4. Duplicate composite key check
    if "gateway_id" in features_df.columns and "decision_week" in features_df.columns:
        dups = features_df.duplicated(subset=["gateway_id", "decision_week"]).sum()
        if dups > 0:
            msg = f"DUPLICATE KEY VIOLATION: {dups} duplicate (gateway_id, decision_week) pairs in features"
            checks["duplicate_key_firewall_passed"] = False
            checks["violations"].append(msg)
            checks["passed"] = False
            raise ValueError(msg)

    return checks
