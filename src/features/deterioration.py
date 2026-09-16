"""Innovation 1: Failure Progression & Deterioration Score Engine.

Source Authority & Method:
- Evaluates temporal trajectory of telemetry degradation by comparing recent behavior
  (trailing 7 days [T - 7d, T)) against pre-decision historical baseline (prior 21 days [T - 28d, T - 7d)).
- All observations strictly satisfy ts_utc < T (Zero Lookahead Temporal Firewall).
- Produces individual trend delta features and a bounded, composite Deterioration Score in [0.0, 1.0].
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)

WEEKLY_HOURS = 168
PRIOR_HISTORY_DAYS = 21  # 3 weeks preceding recent week (days 8 to 28)


def extract_deterioration_features_for_week(
    decision_time: pd.Timestamp | str,
    telemetry_df: pd.DataFrame,
    eligible_gateways: set[str] | list[str] | None = None,
    lookback_days: int = 28,
) -> pd.DataFrame:
    """Extract temporal deterioration metrics comparing recent 7d vs prior 21d history.

    Args:
        decision_time: Monday 00:00:00 UTC decision boundary.
        telemetry_df: Telemetry DataFrame containing observations.
        eligible_gateways: Optional set of active, commissioned gateways.
        lookback_days: Total lookback window in days (default: 28 days = 7d recent + 21d prior).

    Returns:
        pd.DataFrame containing gateway_id, decision_week, and deterioration feature columns.
    """
    decision_dt = pd.Timestamp(decision_time)
    if decision_dt.tz is not None:
        decision_dt = decision_dt.tz_localize(None)

    recent_start = decision_dt - pd.Timedelta(days=7)
    prior_start = decision_dt - pd.Timedelta(days=lookback_days)

    # Filter telemetry strictly inside [prior_start, decision_dt)
    t_df = telemetry_df
    if not t_df.empty:
        if not pd.api.types.is_datetime64_any_dtype(t_df["ts_utc"]):
            t_df = t_df.copy()
            t_df["ts_utc"] = pd.to_datetime(t_df["ts_utc"])
        if t_df["ts_utc"].dt.tz is not None:
            t_df = t_df.copy()
            t_df["ts_utc"] = t_df["ts_utc"].dt.tz_localize(None)

    window_df = t_df[
        (t_df["ts_utc"] >= prior_start) & (t_df["ts_utc"] < decision_dt)
    ].copy()

    if not window_df.empty and "gateway_id" in window_df.columns:
        sample_id = str(window_df["gateway_id"].iloc[0])
        if len(sample_id) != 12 or ":" in sample_id:
            window_df["gateway_id"] = normalize_series(window_df["gateway_id"], target_format="bare")

    # Split into recent (trailing 7d) and prior (21d)
    recent_df = window_df[window_df["ts_utc"] >= recent_start]
    prior_df = window_df[window_df["ts_utc"] < recent_start]

    recent_by_gw = {gw: grp for gw, grp in recent_df.groupby("gateway_id")}
    prior_by_gw = {gw: grp for gw, grp in prior_df.groupby("gateway_id")}

    # Gateway universe
    if eligible_gateways is not None:
        target_gws = sorted(list(eligible_gateways))
    else:
        target_gws = sorted(list(set(recent_by_gw.keys()).union(prior_by_gw.keys())))

    records: list[dict[str, Any]] = []

    for gw in target_gws:
        r_telem = recent_by_gw.get(gw)
        p_telem = prior_by_gw.get(gw)

        # 1. Recent 7-day metrics
        if r_telem is not None and len(r_telem) > 0:
            r_timestamps = set(r_telem["ts_utc"].dt.floor("h"))
            r_obs_hours = min(WEEKLY_HOURS, len(r_timestamps))
            r_missing_hours = max(0, WEEKLY_HOURS - r_obs_hours)
            r_raw_offline_sec = float(r_telem["offline_duration_sec"].max()) if "offline_duration_sec" in r_telem.columns else 0.0
            r_offline_hours = min(168.0, max(0.0, r_raw_offline_sec) / 3600.0)
            r_disconns = int(r_telem["disconnection_cnt"].max()) if "disconnection_cnt" in r_telem.columns else 0
            r_power_cycles = int(r_telem["r_cnt_power_cycle"].sum()) if "r_cnt_power_cycle" in r_telem.columns else 0
            r_reboots = int(r_telem["reboot_cnt"].sum()) if "reboot_cnt" in r_telem.columns else 0
            r_rssi_bad = float(r_telem["rssi_bad"].mean()) if "rssi_bad" in r_telem.columns else 0.0
            r_load1 = float(r_telem["avg_load1"].mean()) if "avg_load1" in r_telem.columns else 0.0
        else:
            # Complete recent silence
            r_obs_hours = 0
            r_missing_hours = WEEKLY_HOURS
            r_offline_hours = 0.0
            r_disconns = 0
            r_power_cycles = 0
            r_reboots = 0
            r_rssi_bad = 0.0
            r_load1 = 0.0

        # 2. Prior 21-day historical metrics (normalized to weekly equivalent)
        # Prior window has 21 days = 3 weekly equivalents
        prior_weeks_factor = 3.0
        if p_telem is not None and len(p_telem) > 0:
            p_timestamps = set(p_telem["ts_utc"].dt.floor("h"))
            p_total_obs = len(p_timestamps)
            p_expected_hours = PRIOR_HISTORY_DAYS * 24  # 504 hours
            p_missing_hours = max(0, p_expected_hours - p_total_obs)
            p_missing_weekly_avg = p_missing_hours / prior_weeks_factor
            
            p_raw_offline_sec = float(p_telem["offline_duration_sec"].max()) if "offline_duration_sec" in p_telem.columns else 0.0
            p_offline_hours = min(168.0, max(0.0, p_raw_offline_sec) / 3600.0)
            p_disconns_weekly_avg = (float(p_telem["disconnection_cnt"].sum()) / prior_weeks_factor) if "disconnection_cnt" in p_telem.columns else 0.0
            p_power_cycles_weekly_avg = (float(p_telem["r_cnt_power_cycle"].sum()) / prior_weeks_factor) if "r_cnt_power_cycle" in p_telem.columns else 0.0
            p_reboots_weekly_avg = (float(p_telem["reboot_cnt"].sum()) / prior_weeks_factor) if "reboot_cnt" in p_telem.columns else 0.0
            p_rssi_bad = float(p_telem["rssi_bad"].mean()) if "rssi_bad" in p_telem.columns else 0.0
            p_load1 = float(p_telem["avg_load1"].mean()) if "avg_load1" in p_telem.columns else 0.0
            has_prior_history = 1.0
        else:
            # Cold start: no prior history in days 8-28
            p_missing_weekly_avg = 0.0
            p_offline_hours = 0.0
            p_disconns_weekly_avg = 0.0
            p_power_cycles_weekly_avg = 0.0
            p_reboots_weekly_avg = 0.0
            p_rssi_bad = 0.0
            p_load1 = 0.0
            has_prior_history = 0.0

        # 3. Compute Delta & Progression Features
        delta_missing_hours = r_missing_hours - p_missing_weekly_avg
        delta_offline_hours = r_offline_hours - p_offline_hours
        delta_disconnections = r_disconns - p_disconns_weekly_avg
        delta_power_cycles = r_power_cycles - p_power_cycles_weekly_avg
        delta_reboots = r_reboots - p_reboots_weekly_avg
        delta_rssi_bad = r_rssi_bad - p_rssi_bad
        delta_load1 = r_load1 - p_load1

        # Normalized progression metrics (percentage worsening)
        norm_missing_surge = max(0.0, delta_missing_hours) / (p_missing_weekly_avg + 12.0)
        norm_offline_surge = max(0.0, delta_offline_hours) / (p_offline_hours + 4.0)
        norm_reboot_surge = max(0.0, delta_reboots) / (p_reboots_weekly_avg + 2.0)

        # 4. Composite Bounded Deterioration Score in [0.0, 1.0]
        # Multi-factor sigmoid combination calibrated to physical failure onsets
        # Components:
        # - Silence surge (sudden drop in communication)
        # - Offline duration surge (sudden long outage event)
        # - Hardware restart surge (power cycle burst)
        raw_det = (
            0.35 * np.clip(delta_missing_hours / 48.0, 0.0, 2.0)
            + 0.30 * np.clip(delta_offline_hours / 24.0, 0.0, 2.0)
            + 0.20 * np.clip(delta_power_cycles / 3.0, 0.0, 2.0)
            + 0.15 * np.clip(delta_disconnections / 10.0, 0.0, 2.0)
        )
        # Scale through logistic function centered at moderate surge (raw = 0.5)
        det_score = float(1.0 / (1.0 + np.exp(-3.0 * (raw_det - 0.5))))

        rec = {
            "gateway_id": gw,
            "decision_week": decision_dt,
            "feat_det_has_history": has_prior_history,
            "feat_det_missing_hours_delta": round(delta_missing_hours, 2),
            "feat_det_offline_hours_delta": round(delta_offline_hours, 2),
            "feat_det_disconns_delta": round(delta_disconnections, 2),
            "feat_det_power_cycles_delta": round(delta_power_cycles, 2),
            "feat_det_reboots_delta": round(delta_reboots, 2),
            "feat_det_rssi_bad_delta": round(delta_rssi_bad, 3),
            "feat_det_load1_delta": round(delta_load1, 3),
            "feat_det_norm_missing_surge": round(norm_missing_surge, 3),
            "feat_det_norm_offline_surge": round(norm_offline_surge, 3),
            "feat_det_norm_reboot_surge": round(norm_reboot_surge, 3),
            "feat_deterioration_score": round(det_score, 4),
        }
        records.append(rec)

    return pd.DataFrame(records)


def get_deterioration_feature_columns() -> list[str]:
    """Return the list of engineered deterioration feature names."""
    return [
        "feat_det_has_history",
        "feat_det_missing_hours_delta",
        "feat_det_offline_hours_delta",
        "feat_det_disconns_delta",
        "feat_det_power_cycles_delta",
        "feat_det_reboots_delta",
        "feat_det_rssi_bad_delta",
        "feat_det_load1_delta",
        "feat_det_norm_missing_surge",
        "feat_det_norm_offline_surge",
        "feat_det_norm_reboot_surge",
        "feat_deterioration_score",
    ]
