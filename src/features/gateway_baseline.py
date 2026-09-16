"""Innovation 3: Gateway-Specific Historical Baseline Engine.

Source Authority & Method:
- Evaluates deviations of a gateway's recent 7-day behavior against its OWN historical operating distribution.
- History Window: Pre-decision historical period strictly prior to the current week: [T - history_days, T - 7d).
- All observations strictly satisfy ts_utc < T (Zero Lookahead Temporal Firewall).
- Minimum history requirement: If a gateway has fewer than min_history_hours of historical records,
  the engine seamlessly falls back to fleet-wide global distribution (Cold-Start Guard).
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_DAYS = 28
DEFAULT_MIN_HISTORY_HOURS = 72  # Minimum 3 days of historical telemetry required


def extract_gateway_baselines_for_week(
    decision_time: pd.Timestamp | str,
    telemetry_df: pd.DataFrame,
    eligible_gateways: set[str] | list[str] | None = None,
    history_days: int = DEFAULT_HISTORY_DAYS,
    min_history_hours: int = DEFAULT_MIN_HISTORY_HOURS,
) -> pd.DataFrame:
    """Extract gateway-relative deviation metrics comparing recent 7d vs gateway's self-history.

    Args:
        decision_time: Monday 00:00:00 UTC decision boundary.
        telemetry_df: Raw or pre-loaded telemetry DataFrame.
        eligible_gateways: Optional set of active gateway IDs.
        history_days: Historical reference baseline depth in days (default: 28 days).
        min_history_hours: Minimum hours of history to qualify for adaptive baseline (default: 72h).

    Returns:
        pd.DataFrame containing gateway_id, decision_week, and gateway-relative feature columns.
    """
    decision_dt = pd.Timestamp(decision_time)
    if decision_dt.tz is not None:
        decision_dt = decision_dt.tz_localize(None)

    recent_start = decision_dt - pd.Timedelta(days=7)
    hist_start = decision_dt - pd.Timedelta(days=history_days)

    t_df = telemetry_df
    if not t_df.empty:
        if not pd.api.types.is_datetime64_any_dtype(t_df["ts_utc"]):
            t_df = t_df.copy()
            t_df["ts_utc"] = pd.to_datetime(t_df["ts_utc"])
        if t_df["ts_utc"].dt.tz is not None:
            t_df = t_df.copy()
            t_df["ts_utc"] = t_df["ts_utc"].dt.tz_localize(None)

    # Window covers [hist_start, decision_dt)
    window_df = t_df[
        (t_df["ts_utc"] >= hist_start) & (t_df["ts_utc"] < decision_dt)
    ].copy()

    if not window_df.empty and "gateway_id" in window_df.columns:
        sample_id = str(window_df["gateway_id"].iloc[0])
        if len(sample_id) != 12 or ":" in sample_id:
            window_df["gateway_id"] = normalize_series(window_df["gateway_id"], target_format="bare")

    # Split into recent week [recent_start, decision_dt) and self-history [hist_start, recent_start)
    recent_df = window_df[window_df["ts_utc"] >= recent_start]
    hist_df = window_df[window_df["ts_utc"] < recent_start]

    recent_by_gw = {gw: grp for gw, grp in recent_df.groupby("gateway_id")}
    hist_by_gw = {gw: grp for gw, grp in hist_df.groupby("gateway_id")}

    # Fleet-wide global historical statistics for fallback (cold start)
    global_offline_mean = float(hist_df["offline_duration_sec"].mean()) if not hist_df.empty and "offline_duration_sec" in hist_df.columns else 0.0
    global_offline_std = float(hist_df["offline_duration_sec"].std()) if not hist_df.empty and "offline_duration_sec" in hist_df.columns else 1.0
    global_disconn_mean = float(hist_df["disconnection_cnt"].mean()) if not hist_df.empty and "disconnection_cnt" in hist_df.columns else 0.0
    global_disconn_std = float(hist_df["disconnection_cnt"].std()) if not hist_df.empty and "disconnection_cnt" in hist_df.columns else 1.0
    global_reboot_mean = float(hist_df["reboot_cnt"].mean()) if not hist_df.empty and "reboot_cnt" in hist_df.columns else 0.0
    global_reboot_std = float(hist_df["reboot_cnt"].std()) if not hist_df.empty and "reboot_cnt" in hist_df.columns else 1.0

    if eligible_gateways is not None:
        target_gws = sorted(list(eligible_gateways))
    else:
        target_gws = sorted(list(set(recent_by_gw.keys()).union(hist_by_gw.keys())))

    records: list[dict[str, Any]] = []

    for gw in target_gws:
        r_grp = recent_by_gw.get(gw)
        h_grp = hist_by_gw.get(gw)

        # Recent 7d aggregates
        if r_grp is not None and len(r_grp) > 0:
            r_offline_peak = min(168.0, float(r_grp["offline_duration_sec"].max()) / 3600.0) if "offline_duration_sec" in r_grp.columns else 0.0
            r_disconn_peak = float(r_grp["disconnection_cnt"].max()) if "disconnection_cnt" in r_grp.columns else 0.0
            r_reboot_tot = float(r_grp["reboot_cnt"].sum()) if "reboot_cnt" in r_grp.columns else 0.0
            r_power_cycle_tot = float(r_grp["r_cnt_power_cycle"].sum()) if "r_cnt_power_cycle" in r_grp.columns else 0.0
            r_obs_hours = len(set(r_grp["ts_utc"].dt.floor("h")))
            r_missing_hours = max(0, 168 - r_obs_hours)
        else:
            r_offline_peak = 0.0
            r_disconn_peak = 0.0
            r_reboot_tot = 0.0
            r_power_cycle_tot = 0.0
            r_missing_hours = 168.0

        # Gateway's self-history aggregates
        h_obs_hours = len(set(h_grp["ts_utc"].dt.floor("h"))) if h_grp is not None and len(h_grp) > 0 else 0

        if h_grp is not None and h_obs_hours >= min_history_hours:
            # Sufficient history: compute gateway-specific baseline
            has_adequate_history = 1.0
            # Weekly equivalents in prior window (21 days = 3 weeks)
            h_offline_hist_peak = min(168.0, float(h_grp["offline_duration_sec"].max()) / 3600.0) if "offline_duration_sec" in h_grp.columns else 0.0
            h_offline_mean = float(h_grp["offline_duration_sec"].mean() / 3600.0) if "offline_duration_sec" in h_grp.columns else 0.0
            h_offline_std = max(1.0, float(h_grp["offline_duration_sec"].std() / 3600.0)) if "offline_duration_sec" in h_grp.columns else 1.0

            h_disconn_mean = float(h_grp["disconnection_cnt"].mean()) if "disconnection_cnt" in h_grp.columns else 0.0
            h_disconn_std = max(1.0, float(h_grp["disconnection_cnt"].std())) if "disconnection_cnt" in h_grp.columns else 1.0

            h_reboot_weekly = (float(h_grp["reboot_cnt"].sum()) / 3.0) if "reboot_cnt" in h_grp.columns else 0.0
            h_reboot_std = max(1.0, float(h_grp["reboot_cnt"].std())) if "reboot_cnt" in h_grp.columns else 1.0

            h_expected_hist_hours = (history_days - 7) * 24
            h_missing_weekly = max(0.0, (h_expected_hist_hours - h_obs_hours) / 3.0)

            # Gateway relative Z-scores
            z_offline = (r_offline_peak - h_offline_mean) / (h_offline_std + 0.1)
            z_disconns = (r_disconn_peak - h_disconn_mean) / (h_disconn_std + 0.1)
            z_reboots = (r_reboot_tot - h_reboot_weekly) / (h_reboot_std + 0.1)
            z_missing = (r_missing_hours - h_missing_weekly) / 12.0
        else:
            # Cold start fallback: use global fleet distributions
            has_adequate_history = 0.0
            z_offline = (r_offline_peak - (global_offline_mean / 3600.0)) / (max(1.0, global_offline_std / 3600.0) + 0.1)
            z_disconns = (r_disconn_peak - global_disconn_mean) / (max(1.0, global_disconn_std) + 0.1)
            z_reboots = (r_reboot_tot - (global_reboot_mean * 7.0)) / (max(1.0, global_reboot_std * 7.0) + 0.1)
            z_missing = (r_missing_hours - 22.0) / 12.0

        # Clip Z-scores to prevent outlier skew
        z_offline = float(np.clip(z_offline, -3.0, 5.0))
        z_disconns = float(np.clip(z_disconns, -3.0, 5.0))
        z_reboots = float(np.clip(z_reboots, -3.0, 5.0))
        z_missing = float(np.clip(z_missing, -3.0, 5.0))

        # Composite Gateway-Relative Anomaly Score in [0.0, 1.0]
        # Sum of positive Z-score deviations (breaches above gateway's normal behavior)
        pos_deviations = max(0.0, z_offline) + max(0.0, z_disconns) + max(0.0, z_reboots) + max(0.0, z_missing)
        # Logistic map centered at 2 sigma cumulative deviation
        gw_rel_anomaly_score = float(1.0 / (1.0 + np.exp(-1.5 * (pos_deviations - 2.0))))

        rec = {
            "gateway_id": gw,
            "decision_week": decision_dt,
            "feat_gw_has_adequate_history": has_adequate_history,
            "feat_gw_hist_obs_hours": h_obs_hours,
            "feat_gw_z_offline": round(z_offline, 3),
            "feat_gw_z_disconns": round(z_disconns, 3),
            "feat_gw_z_reboots": round(z_reboots, 3),
            "feat_gw_z_missing": round(z_missing, 3),
            "feat_gw_relative_anomaly_score": round(gw_rel_anomaly_score, 4),
        }
        records.append(rec)

    return pd.DataFrame(records)


def get_gateway_baseline_feature_columns() -> list[str]:
    """Return the list of gateway-specific baseline feature columns."""
    return [
        "feat_gw_has_adequate_history",
        "feat_gw_hist_obs_hours",
        "feat_gw_z_offline",
        "feat_gw_z_disconns",
        "feat_gw_z_reboots",
        "feat_gw_z_missing",
        "feat_gw_relative_anomaly_score",
    ]
