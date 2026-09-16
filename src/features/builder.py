"""Leakage-safe feature engineering pipeline and feature matrix builder.

Source Authority:
- [CONFIRMED BY LPDG - Temporal Cutoff Rule]:
  Predictions for each week are generated at Monday 00:00:00 UTC using strictly t < Monday.
  Zero future telemetry, meter reads, or visit outcomes may be accessed.
- [OBSERVED IN DATA - Stages 1, 2, 3]:
  1. 1-3h silence is baseline jitter; streaks >= 12h and tail silence >= 24h are strong indicators.
  2. Offline duration transfer function exhibits candidate breakpoint at >= 24h/week.
  3. Power-cycle reboots (r_cnt_power_cycle) are 13.4x elevated in genuine repairs.
  4. Yagi 9dBi antennas confound raw packet counts (85x higher traffic); cellular RSSI bad and tx_success carry true signal.
  5. 12 future-installed gateways (mid-2026) and 12 decommissioned gateways must be masked.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from src.data.time_grid import build_hourly_grid, compute_silence_spells, find_missing_hours
from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)

# Standard 1-week lookback in hours
WEEKLY_HOURS = 168


def extract_features_for_decision_week(
    decision_time: pd.Timestamp | str,
    telemetry_df: pd.DataFrame,
    master_df: pd.DataFrame,
    engineer_review_df: pd.DataFrame | None = None,
    lookback_days: int = 7,
) -> pd.DataFrame:
    """Extract strictly backward-looking features for all eligible gateways at a given decision boundary.

    Observation interval: [decision_time - lookback_days, decision_time)
    Upper bound: decision_time - 1 second (strictly t < decision_time).

    Args:
        decision_time: The exact Monday 00:00:00 UTC decision timestamp.
        telemetry_df: Raw or partitioned telemetry observations.
        master_df: Gateway master records (installed_on, decommissioned_on, antenna_type, site_type, n_meters_installed).
        engineer_review_df: Optional engineer review snapshot (accessible strictly on or after 2026-02-15).
        lookback_days: Lookback window length in days (default: 7 days / 168 hours).

    Returns:
        pd.DataFrame containing engineered features for all eligible active gateways at decision_time.
    """
    decision_dt = pd.to_datetime(decision_time)
    if decision_dt.tzinfo is not None:
        decision_dt = decision_dt.tz_localize(None)

    window_start = decision_dt - pd.Timedelta(days=lookback_days)
    observation_cutoff = decision_dt - pd.Timedelta(seconds=1)

    # 1. Master normalization and lifecycle eligibility filtering
    m_df = master_df.copy()
    m_df["gateway_id"] = normalize_series(m_df["gateway_id"], target_format="bare")
    if "installed_on" in m_df.columns:
        m_df["installed_on"] = pd.to_datetime(m_df["installed_on"]).dt.tz_localize(None)
    if "decommissioned_on" in m_df.columns:
        m_df["decommissioned_on"] = pd.to_datetime(m_df["decommissioned_on"]).dt.tz_localize(None)

    # Lifecycle Mask: Must be installed on or before decision_dt, and not decommissioned prior to decision_dt
    installed_mask = m_df["installed_on"].isna() | (m_df["installed_on"] <= decision_dt)
    not_decommissioned_mask = m_df["decommissioned_on"].isna() | (m_df["decommissioned_on"] >= decision_dt)
    eligible_master = m_df[installed_mask & not_decommissioned_mask].copy()
    eligible_gateways = set(eligible_master["gateway_id"].unique())

    # 2. Strict temporal filtering on telemetry
    t_df = telemetry_df
    # Only copy and normalize if not already pre-normalized
    if not t_df.empty:
        sample_id = str(t_df["gateway_id"].iloc[0])
        if len(sample_id) != 12 or ":" in sample_id:
            t_df = t_df.copy()
            t_df["gateway_id"] = normalize_series(t_df["gateway_id"], target_format="bare")
        
        if not pd.api.types.is_datetime64_any_dtype(t_df["ts_utc"]):
            t_df = t_df.copy()
            t_df["ts_utc"] = pd.to_datetime(t_df["ts_utc"])
        
        if t_df["ts_utc"].dt.tz is not None:
            t_df = t_df.copy()
            t_df["ts_utc"] = t_df["ts_utc"].dt.tz_localize(None)

    # Filter telemetry strictly inside [window_start, decision_dt)
    telem_window = t_df[
        (t_df["ts_utc"] >= window_start) & (t_df["ts_utc"] < decision_dt)
    ]

    # Pre-aggregate telemetry per gateway
    # Group by gateway for fast metric calculation
    telem_by_gw = {gw: grp for gw, grp in telem_window.groupby("gateway_id")}

    records: list[dict[str, Any]] = []

    for _, master_row in eligible_master.iterrows():
        gw = master_row["gateway_id"]
        rec: dict[str, Any] = {
            "gateway_id": gw,
            "decision_week": decision_dt,
            "observation_cutoff_utc": observation_cutoff,
        }

        # Static Metadata Features
        n_meters = master_row.get("n_meters_installed", 180)
        rec["feat_n_meters_installed"] = int(n_meters) if pd.notna(n_meters) else 180

        installed_on = master_row.get("installed_on")
        if pd.notna(installed_on):
            age_days = (decision_dt - installed_on).days
            rec["feat_installation_age_days"] = max(0, age_days)
        else:
            rec["feat_installation_age_days"] = 365

        # Antenna one-hot encoding
        antenna = str(master_row.get("antenna_type", "Omni 3dBi"))
        rec["feat_antenna_Omni_3dBi"] = int("Omni 3dBi" in antenna)
        rec["feat_antenna_Omni_5dBi"] = int("Omni 5dBi" in antenna)
        rec["feat_antenna_Panel_7dBi"] = int("Panel 7dBi" in antenna)
        rec["feat_antenna_Yagi_9dBi"] = int("Yagi 9dBi" in antenna)

        # Site type one-hot encoding (maps German categories in gateway_master: Gebäude, Heizraum, Kellerraum, Außenmast, Schaltschrank)
        site = str(master_row.get("site_type", "Outdoor")).lower()
        rec["feat_site_Indoor"] = int(any(k in site for k in ["indoor", "geb", "heiz", "keller"]))
        rec["feat_site_Outdoor"] = int(any(k in site for k in ["outdoor", "aussen", "außen", "schalt"]))
        rec["feat_site_Pole"] = int(any(k in site for k in ["pole", "mast"]))
        rec["feat_site_Rooftop"] = int(any(k in site for k in ["rooftop", "dach"]))

        # Telemetry metrics
        gw_telem = telem_by_gw.get(gw)

        if gw_telem is None or len(gw_telem) == 0:
            # Total silence (0 telemetry rows in entire trailing week)
            rec["feat_observed_hours"] = 0
            rec["feat_missing_hours"] = WEEKLY_HOURS
            rec["feat_missing_ratio"] = 1.0
            rec["feat_max_silence_streak"] = WEEKLY_HOURS
            rec["feat_tail_silence"] = WEEKLY_HOURS
            rec["feat_silence_spell_count"] = 1

            # Backhaul
            rec["feat_sum_offline_sec"] = 0.0
            rec["feat_offline_hours"] = 0.0
            rec["feat_offline_ge_24h"] = 0
            rec["feat_sum_disconnections"] = 0

            # Reboots
            rec["feat_reboot_cnt_total"] = 0
            rec["feat_power_cycle_cnt"] = 0
            rec["feat_sw_reboot_cnt"] = 0
            rec["feat_unknown_reboot_cnt"] = 0
            rec["feat_max_reboot_1h"] = 0
            rec["feat_power_cycle_recent_24h"] = 0

            # Radio & OS
            rec["feat_mean_rssi_bad"] = 0.0
            rec["feat_tot_tx_success"] = 0
            rec["feat_mean_load1"] = 0.0
            rec["feat_min_memfree"] = 0.0
        else:
            # Observed telemetry present
            # Distinct hourly buckets where telemetry was recorded (strictly <= 168h)
            timestamps_set = set(gw_telem["ts_utc"].dt.floor("h"))
            full_grid = pd.date_range(window_start, decision_dt - pd.Timedelta(hours=1), freq="h")
            missing_bools = [ts not in timestamps_set for ts in full_grid]

            distinct_obs_hours = len(timestamps_set)
            rec["feat_observed_hours"] = min(WEEKLY_HOURS, distinct_obs_hours)
            missing_hrs = sum(missing_bools)
            rec["feat_missing_hours"] = missing_hrs
            rec["feat_missing_ratio"] = missing_hrs / float(WEEKLY_HOURS)

            # Compute max streak, tail silence, and spell count
            max_streak = 0
            curr_streak = 0
            spell_cnt = 0
            in_spell = False

            for is_missing in missing_bools:
                if is_missing:
                    curr_streak += 1
                    max_streak = max(max_streak, curr_streak)
                    if not in_spell:
                        spell_cnt += 1
                        in_spell = True
                else:
                    curr_streak = 0
                    in_spell = False

            rec["feat_max_silence_streak"] = max_streak
            rec["feat_silence_spell_count"] = spell_cnt

            # Tail silence: count backwards from end of week
            tail_streak = 0
            for is_missing in reversed(missing_bools):
                if is_missing:
                    tail_streak += 1
                else:
                    break
            rec["feat_tail_silence"] = tail_streak

            # Backhaul offline metrics:
            # Empirical audit demonstrates offline_duration_sec is a cached/register snapshot of the last disconnection
            # event duration rather than an hourly increment. Summing it duplicates frozen values across consecutive packets,
            # producing physically impossible values (>168h in a 7-day week).
            # We take the peak event duration in the week, bounded strictly by wall-clock time (168 hours = 604,800 sec).
            if "offline_duration_sec" in gw_telem.columns and len(gw_telem) > 0:
                raw_max_offline_sec = float(gw_telem["offline_duration_sec"].max())
                offline_sec = min(float(WEEKLY_HOURS * 3600), max(0.0, raw_max_offline_sec))
            else:
                offline_sec = 0.0

            rec["feat_sum_offline_sec"] = offline_sec
            offline_hrs = offline_sec / 3600.0
            rec["feat_offline_hours"] = offline_hrs
            rec["feat_offline_ge_24h"] = int(offline_hrs >= 24.0)

            # Peak disconnection intensity in trailing week
            if "disconnection_cnt" in gw_telem.columns and len(gw_telem) > 0:
                rec["feat_sum_disconnections"] = int(gw_telem["disconnection_cnt"].max())
            else:
                rec["feat_sum_disconnections"] = 0

            # Reboot attribution
            rec["feat_reboot_cnt_total"] = int(gw_telem["reboot_cnt"].sum()) if "reboot_cnt" in gw_telem.columns else 0
            rec["feat_power_cycle_cnt"] = int(gw_telem["r_cnt_power_cycle"].sum()) if "r_cnt_power_cycle" in gw_telem.columns else 0
            rec["feat_sw_reboot_cnt"] = int(gw_telem["r_cnt_reboot"].sum()) if "r_cnt_reboot" in gw_telem.columns else 0
            rec["feat_unknown_reboot_cnt"] = int(gw_telem["r_cnt_unknown"].sum()) if "r_cnt_unknown" in gw_telem.columns else 0
            rec["feat_max_reboot_1h"] = int(gw_telem["reboot_cnt"].max()) if "reboot_cnt" in gw_telem.columns else 0

            # Power cycles in recent 24h
            recent_24h_start = decision_dt - pd.Timedelta(hours=24)
            recent_telem = gw_telem[gw_telem["ts_utc"] >= recent_24h_start]
            rec["feat_power_cycle_recent_24h"] = (
                int(recent_telem["r_cnt_power_cycle"].sum()) if "r_cnt_power_cycle" in recent_telem.columns else 0
            )

            # Radio metrics
            rec["feat_mean_rssi_bad"] = float(gw_telem["rssi_bad"].mean()) if "rssi_bad" in gw_telem.columns else 0.0
            rec["feat_tot_tx_success"] = int(gw_telem["tx_success"].sum()) if "tx_success" in gw_telem.columns else 0
            rec["feat_mean_load1"] = float(gw_telem["avg_load1"].mean()) if "avg_load1" in gw_telem.columns else 0.0
            rec["feat_min_memfree"] = float(gw_telem["avg_memfree"].min()) if "avg_memfree" in gw_telem.columns else 0.0

        # Optional Engineer Review Feature: Gated strictly on or after 2026-02-15
        if engineer_review_df is not None and decision_dt >= pd.Timestamp("2026-02-15"):
            er = engineer_review_df.copy()
            er["gateway_id"] = normalize_series(er["gateway_id"], target_format="bare")
            match = er[er["gateway_id"] == gw]
            if len(match) > 0 and "priority" in match.columns:
                rec["feat_engineer_priority_score"] = float(match["priority"].iloc[0]) if pd.notna(match["priority"].iloc[0]) else 0.0
            else:
                rec["feat_engineer_priority_score"] = 0.0
        else:
            rec["feat_engineer_priority_score"] = 0.0

        records.append(rec)

    return pd.DataFrame(records)


def build_feature_matrix(
    decision_weeks: list[pd.Timestamp | str],
    telemetry_df: pd.DataFrame,
    master_df: pd.DataFrame,
    engineer_review_df: pd.DataFrame | None = None,
    lookback_days: int = 7,
) -> pd.DataFrame:
    """Construct multi-week feature matrix across multiple decision boundaries.

    Args:
        decision_weeks: List of Monday 00:00:00 UTC timestamps.
        telemetry_df: Full or subset telemetry DataFrame.
        master_df: Gateway master records.
        engineer_review_df: Optional engineer review records.
        lookback_days: Trailing window in days.

    Returns:
        pd.DataFrame containing stacked feature records across all requested decision weeks.
    """
    # Pre-normalize telemetry once for massive speedup
    t_df = telemetry_df.copy()
    if not t_df.empty:
        t_df["gateway_id"] = normalize_series(t_df["gateway_id"], target_format="bare")
        t_df["ts_utc"] = pd.to_datetime(t_df["ts_utc"])
        if t_df["ts_utc"].dt.tz is not None:
            t_df["ts_utc"] = t_df["ts_utc"].dt.tz_localize(None)

    m_df = master_df.copy()
    m_df["gateway_id"] = normalize_series(m_df["gateway_id"], target_format="bare")

    dfs = []
    for dw in decision_weeks:
        df_week = extract_features_for_decision_week(
            decision_time=dw,
            telemetry_df=t_df,
            master_df=m_df,
            engineer_review_df=engineer_review_df,
            lookback_days=lookback_days,
        )
        dfs.append(df_week)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def get_feature_family_columns() -> dict[str, list[str]]:
    """Return catalog of engineered feature columns grouped by operational domain family."""
    availability_cols = [
        "feat_missing_hours",
        "feat_missing_ratio",
        "feat_max_silence_streak",
        "feat_tail_silence",
        "feat_silence_spell_count",
        "feat_sum_offline_sec",
        "feat_offline_hours",
        "feat_offline_ge_24h",
        "feat_sum_disconnections",
    ]
    stability_cols = [
        "feat_reboot_cnt_total",
        "feat_power_cycle_cnt",
        "feat_sw_reboot_cnt",
        "feat_unknown_reboot_cnt",
        "feat_max_reboot_1h",
        "feat_power_cycle_recent_24h",
    ]
    radio_cols = [
        "feat_mean_rssi_bad",
        "feat_tot_tx_success",
        "feat_mean_load1",
        "feat_min_memfree",
    ]
    static_cols = [
        "feat_n_meters_installed",
        "feat_installation_age_days",
        "feat_antenna_Omni_3dBi",
        "feat_antenna_Omni_5dBi",
        "feat_antenna_Panel_7dBi",
        "feat_antenna_Yagi_9dBi",
        "feat_site_Indoor",
        "feat_site_Outdoor",
        "feat_site_Pole",
        "feat_site_Rooftop",
    ]
    all_cols = availability_cols + stability_cols + radio_cols + static_cols

    return {
        "availability": availability_cols,
        "stability": stability_cols,
        "radio": radio_cols,
        "static": static_cols,
        "all": all_cols,
    }
