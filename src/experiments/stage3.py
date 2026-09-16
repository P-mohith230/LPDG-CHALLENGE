"""Stage 3 Empirical Research Experiments & Hypothesis Testing.

Implements the four formal Round 2 research experiments and cross-analysis
stipulated in the project implementation plan:
- E-01: Telemetry Silence Investigation (RQ-02)
- E-03: Offline Duration Transfer Function (RQ-07)
- E-04: Reboot Cause Attribution (RQ-08)
- E-05: Radio Quality & CRC Noise (RQ-11)
- Cross-Analysis: Cross-signal relationships and lifecycle cohort dynamics.

All experiments strictly enforce temporal ordering: signal observation windows
precede outcome measurement windows without future information leakage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.data.loader import (
    load_field_visits,
    load_gateway_master,
    load_meter_read_success,
    load_telemetry,
)

DEFAULT_HISTORICAL_MONTHS = [
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
]


def _extract_silence_features_for_weeks(
    telem_df: pd.DataFrame, mr_weeks: List[pd.Timestamp]
) -> pd.DataFrame:
    """Extract weekly silence features (spells, streaks, tail silence) from telemetry."""
    df = telem_df.copy()
    df["week_start"] = df["ts_utc"].dt.floor("D") - pd.to_timedelta(
        df["ts_utc"].dt.dayofweek, unit="D"
    )
    df["hour_offset"] = (
        (df["ts_utc"] - df["week_start"]).dt.total_seconds() // 3600
    ).astype(int)

    df_sub = df[df["week_start"].isin(mr_weeks)]
    gw_week_hours = (
        df_sub.groupby(["gateway_id", "week_start"])["hour_offset"]
        .apply(set)
        .reset_index()
    )

    records = []
    all_hours = set(range(168))
    for _, row in gw_week_hours.iterrows():
        obs = row["hour_offset"]
        missing = all_hours - obs
        n_missing = len(missing)
        if n_missing == 0:
            records.append(
                {
                    "gateway_id": row["gateway_id"],
                    "week_start": row["week_start"],
                    "n_missing": 0,
                    "n_spells": 0,
                    "max_streak": 0,
                    "tail_silence": 0,
                    "recent_24h_silence": 0,
                }
            )
        else:
            missing_sorted = sorted(missing)
            spells = []
            curr_len = 1
            for i in range(1, len(missing_sorted)):
                if missing_sorted[i] == missing_sorted[i - 1] + 1:
                    curr_len += 1
                else:
                    spells.append(curr_len)
                    curr_len = 1
            spells.append(curr_len)

            tail_silence = 0
            for h in range(167, -1, -1):
                if h in missing:
                    tail_silence += 1
                else:
                    break
            recent_24h = len(missing.intersection(range(144, 168)))
            records.append(
                {
                    "gateway_id": row["gateway_id"],
                    "week_start": row["week_start"],
                    "n_missing": n_missing,
                    "n_spells": len(spells),
                    "max_streak": max(spells),
                    "tail_silence": tail_silence,
                    "recent_24h_silence": recent_24h,
                }
            )
    return pd.DataFrame(records)


def run_experiment_e01(
    data_dir: Path | str | None = None,
    months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Experiment E-01: Telemetry Silence Profiling & Operational Association.

    Investigates whether telemetry silence (omitted rows) contains operationally
    meaningful predictive signal for smart-meter collection deficits.
    """
    months = months or DEFAULT_HISTORICAL_MONTHS
    mr = load_meter_read_success(data_dir=data_dir, normalize_id="bare")
    mr["week_start"] = pd.to_datetime(mr["week_start"]).dt.tz_localize("UTC")

    telem_dir = Path(data_dir) / "telemetry" if data_dir is not None else None
    telem = load_telemetry(
        telemetry_dir=telem_dir,
        months=months,
        columns=["gateway_id", "ts_utc"],
    )

    min_ts = telem["ts_utc"].min()
    max_ts = telem["ts_utc"].max()
    mr = mr[
        (mr["week_start"] >= min_ts)
        & (mr["week_start"] + pd.Timedelta(days=7) <= max_ts + pd.Timedelta(hours=1))
    ].copy()

    silence_df = _extract_silence_features_for_weeks(
        telem, mr["week_start"].unique().tolist()
    )

    merged = pd.merge(mr, silence_df, on=["gateway_id", "week_start"], how="left")
    merged["n_missing"] = merged["n_missing"].fillna(168)
    merged["n_spells"] = merged["n_spells"].fillna(1)
    merged["max_streak"] = merged["max_streak"].fillna(168)
    merged["tail_silence"] = merged["tail_silence"].fillna(168)
    merged["recent_24h_silence"] = merged["recent_24h_silence"].fillna(24)

    merged["read_ratio"] = merged["meters_read"] / merged["meters_expected"]
    merged["zero_read"] = (merged["meters_read"] == 0).astype(int)
    merged["severe_deficit"] = (merged["read_ratio"] < 0.5).astype(int)
    merged["partial_deficit"] = (
        merged["meters_read"] < merged["meters_expected"]
    ).astype(int)

    # Exploratory bins
    bins = [-1, 0, 3, 11, 23, 47, 71, 167, 1000]
    labels = [
        "0h (perfect)",
        "1-3h",
        "4-11h",
        "12-23h",
        "24-47h",
        "48-71h",
        "72-167h",
        ">=168h (total)",
    ]
    merged["streak_bin"] = pd.cut(merged["max_streak"], bins=bins, labels=labels)

    contemporaneous_table = merged.groupby("streak_bin", observed=False).agg(
        n_weeks=("gateway_id", "count"),
        mean_read_ratio=("read_ratio", "mean"),
        zero_read_rate=("zero_read", "mean"),
        zero_read_cnt=("zero_read", "sum"),
        severe_deficit_rate=("severe_deficit", "mean"),
        partial_deficit_rate=("partial_deficit", "mean"),
    )

    # Predictive analysis: week k silence -> week k+1 outcome
    merged_sorted = merged.sort_values(
        ["gateway_id", "week_start"]
    ).reset_index(drop=True)
    merged_sorted["next_read_ratio"] = merged_sorted.groupby("gateway_id")[
        "read_ratio"
    ].shift(-1)
    merged_sorted["next_zero_read"] = merged_sorted.groupby("gateway_id")[
        "zero_read"
    ].shift(-1)
    merged_sorted["next_severe_deficit"] = merged_sorted.groupby("gateway_id")[
        "severe_deficit"
    ].shift(-1)

    pred_df = merged_sorted.dropna(subset=["next_read_ratio"]).copy()
    predictive_streak_table = pred_df.groupby("streak_bin", observed=False).agg(
        n_weeks=("gateway_id", "count"),
        next_mean_read_ratio=("next_read_ratio", "mean"),
        next_zero_read_rate=("next_zero_read", "mean"),
        next_zero_read_cnt=("next_zero_read", "sum"),
        next_severe_deficit_rate=("next_severe_deficit", "mean"),
    )

    pred_df["tail_bin"] = pd.cut(
        pred_df["tail_silence"], bins=bins, labels=labels
    )
    predictive_tail_table = pred_df.groupby("tail_bin", observed=False).agg(
        n_weeks=("gateway_id", "count"),
        next_mean_read_ratio=("next_read_ratio", "mean"),
        next_zero_read_rate=("next_zero_read", "mean"),
        next_zero_read_cnt=("next_zero_read", "sum"),
        next_severe_deficit_rate=("next_severe_deficit", "mean"),
    )

    # Summary statistics
    total_weeks = len(merged)
    baseline_1_3h_pct = float(
        (merged["streak_bin"] == "1-3h").mean() * 100
    )
    correlation_streak_read = float(
        merged["max_streak"].corr(merged["read_ratio"])
    )
    correlation_streak_deficit = float(
        merged["max_streak"].corr(merged["severe_deficit"])
    )
    correlation_tail_deficit = float(
        pred_df["tail_silence"].corr(pred_df["next_severe_deficit"])
    )

    return {
        "experiment_id": "E-01",
        "total_gateway_weeks": total_weeks,
        "evaluable_predictive_weeks": len(pred_df),
        "baseline_1_3h_pct": baseline_1_3h_pct,
        "correlation_streak_read_ratio": correlation_streak_read,
        "correlation_streak_severe_deficit": correlation_streak_deficit,
        "correlation_tail_next_severe_deficit": correlation_tail_deficit,
        "contemporaneous_table": contemporaneous_table,
        "predictive_streak_table": predictive_streak_table,
        "predictive_tail_table": predictive_tail_table,
    }


def run_experiment_e03(
    data_dir: Path | str | None = None,
    months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Experiment E-03: Offline Duration Transfer Function.

    Evaluates the empirical relationship between backhaul downtime
    (offline_duration_sec) and smart meter collection deficit (meters_read / meters_expected).
    """
    months = months or DEFAULT_HISTORICAL_MONTHS
    mr = load_meter_read_success(data_dir=data_dir, normalize_id="bare")
    mr["week_start"] = pd.to_datetime(mr["week_start"]).dt.tz_localize("UTC")

    telem_dir = Path(data_dir) / "telemetry" if data_dir is not None else None
    telem = load_telemetry(
        telemetry_dir=telem_dir,
        months=months,
        columns=[
            "gateway_id",
            "ts_utc",
            "offline_duration_sec",
            "disconnection_cnt",
        ],
    )

    min_ts = telem["ts_utc"].min()
    max_ts = telem["ts_utc"].max()
    mr = mr[
        (mr["week_start"] >= min_ts)
        & (mr["week_start"] + pd.Timedelta(days=7) <= max_ts + pd.Timedelta(hours=1))
    ].copy()

    telem["week_start"] = telem["ts_utc"].dt.floor("D") - pd.to_timedelta(
        telem["ts_utc"].dt.dayofweek, unit="D"
    )
    telem_mr_weeks = telem[telem["week_start"].isin(mr["week_start"].unique())]

    total_rows = len(telem_mr_weeks)
    zero_rows = int((telem_mr_weeks["offline_duration_sec"] == 0).sum())
    zero_pct = float(zero_rows / total_rows * 100)
    row_corr_disc_offline = float(
        telem_mr_weeks["disconnection_cnt"].corr(
            telem_mr_weeks["offline_duration_sec"]
        )
    )

    agg_df = telem_mr_weeks.groupby(["gateway_id", "week_start"]).agg(
        total_offline_sec=("offline_duration_sec", "sum"),
        max_offline_sec=("offline_duration_sec", "max"),
        nonzero_offline_hours=("offline_duration_sec", lambda x: (x > 0).sum()),
        total_disconnections=("disconnection_cnt", "sum"),
        max_disconnections=("disconnection_cnt", "max"),
    ).reset_index()

    m_e03 = pd.merge(mr, agg_df, on=["gateway_id", "week_start"], how="left")
    m_e03["total_offline_sec"] = m_e03["total_offline_sec"].fillna(168 * 3600)
    m_e03["max_offline_sec"] = m_e03["max_offline_sec"].fillna(3600)
    m_e03["nonzero_offline_hours"] = m_e03["nonzero_offline_hours"].fillna(168)
    m_e03["total_disconnections"] = m_e03["total_disconnections"].fillna(0)

    m_e03["read_ratio"] = m_e03["meters_read"] / m_e03["meters_expected"]
    m_e03["severe_deficit"] = (m_e03["read_ratio"] < 0.5).astype(int)
    m_e03["total_offline_hours"] = m_e03["total_offline_sec"] / 3600.0

    bins_off = [-1, 0, 1, 6, 24, 72, 168, 10000]
    labels_off = ["0h", "0-1h", "1-6h", "6-24h", "24-72h", "72-168h", ">168h"]
    m_e03["offline_bin"] = pd.cut(
        m_e03["total_offline_hours"], bins=bins_off, labels=labels_off
    )

    contemporaneous_table = m_e03.groupby("offline_bin", observed=False).agg(
        n_weeks=("gateway_id", "count"),
        mean_read_ratio=("read_ratio", "mean"),
        severe_deficit_rate=("severe_deficit", "mean"),
        mean_disconnections=("total_disconnections", "mean"),
    )

    # Predictive analysis
    m_e03_sorted = m_e03.sort_values(
        ["gateway_id", "week_start"]
    ).reset_index(drop=True)
    m_e03_sorted["next_read_ratio"] = m_e03_sorted.groupby("gateway_id")[
        "read_ratio"
    ].shift(-1)
    m_e03_sorted["next_severe_deficit"] = m_e03_sorted.groupby("gateway_id")[
        "severe_deficit"
    ].shift(-1)
    valid_pred = m_e03_sorted.dropna(subset=["next_read_ratio"]).copy()

    predictive_table = valid_pred.groupby("offline_bin", observed=False).agg(
        n_weeks=("gateway_id", "count"),
        next_mean_read_ratio=("next_read_ratio", "mean"),
        next_severe_deficit_rate=("next_severe_deficit", "mean"),
    )

    weekly_corr_disc_offline = float(
        m_e03["total_disconnections"].corr(m_e03["total_offline_sec"])
    )
    corr_offline_read_ratio = float(
        m_e03["total_offline_sec"].corr(m_e03["read_ratio"])
    )
    corr_offline_severe_deficit = float(
        m_e03["total_offline_sec"].corr(m_e03["severe_deficit"])
    )

    return {
        "experiment_id": "E-03",
        "total_telemetry_rows": total_rows,
        "zero_offline_rows_pct": zero_pct,
        "row_level_disc_offline_corr": row_corr_disc_offline,
        "weekly_disc_offline_corr": weekly_corr_disc_offline,
        "corr_offline_read_ratio": corr_offline_read_ratio,
        "corr_offline_severe_deficit": corr_offline_severe_deficit,
        "contemporaneous_table": contemporaneous_table,
        "predictive_table": predictive_table,
    }


def run_experiment_e04(
    data_dir: Path | str | None = None,
    months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Experiment E-04: Reboot Cause Attribution against Field Visits.

    Investigates reboot types (r_cnt_power_cycle, r_cnt_reboot, r_cnt_unknown)
    relative to technician dispatch reasons, field outcomes, and parts replaced.
    """
    months = months or DEFAULT_HISTORICAL_MONTHS
    fv = load_field_visits(data_dir=data_dir, normalize_id="bare")
    telem_dir = Path(data_dir) / "telemetry" if data_dir is not None else None
    telem = load_telemetry(
        telemetry_dir=telem_dir,
        months=months,
        columns=[
            "gateway_id",
            "ts_utc",
            "reboot_cnt",
            "r_cnt_power_cycle",
            "r_cnt_reboot",
            "r_cnt_unknown",
            "reboot_duration_sec",
        ],
    )

    fv_eval = fv[
        (fv["requested_on"] >= "2025-08-08")
        & (fv["requested_on"] <= "2026-01-31")
    ].copy()

    # Pre-index telemetry for fast lookup by gateway
    telem_by_gw = {
        gid: group for gid, group in telem.groupby("gateway_id")
    }

    trailing_stats = []
    for _, v in fv_eval.iterrows():
        gid = v["gateway_id"]
        req_date = pd.Timestamp(v["requested_on"], tz="UTC")
        t_start = req_date - pd.Timedelta(days=7)

        if gid in telem_by_gw:
            gw_df = telem_by_gw[gid]
            sub = gw_df[(gw_df["ts_utc"] >= t_start) & (gw_df["ts_utc"] < req_date)]
            n_rows = len(sub)
            tot_reboot = int(sub["reboot_cnt"].sum()) if n_rows > 0 else 0
            tot_power = int(sub["r_cnt_power_cycle"].sum()) if n_rows > 0 else 0
            tot_sw = int(sub["r_cnt_reboot"].sum()) if n_rows > 0 else 0
            tot_unk = int(sub["r_cnt_unknown"].sum()) if n_rows > 0 else 0
            max_1h = int(sub["reboot_cnt"].max()) if n_rows > 0 else 0
            tot_dur = float(sub["reboot_duration_sec"].sum()) if n_rows > 0 else 0.0
        else:
            n_rows = 0
            tot_reboot = tot_power = tot_sw = tot_unk = max_1h = 0
            tot_dur = 0.0

        trailing_stats.append(
            {
                "visit_id": v["visit_id"],
                "gateway_id": gid,
                "reason_reported": v["reason_reported"],
                "outcome": v["outcome"],
                "parts_replaced": v["parts_replaced"],
                "n_telem_hours_7d": n_rows,
                "tot_reboot": tot_reboot,
                "tot_power_cycle": tot_power,
                "tot_sw_reboot": tot_sw,
                "tot_unknown": tot_unk,
                "max_reboot_1h": max_1h,
                "tot_reboot_dur_sec": tot_dur,
            }
        )

    df_stats = pd.DataFrame(trailing_stats)

    by_reason = df_stats.groupby("reason_reported").agg(
        n_visits=("visit_id", "count"),
        mean_reboot=("tot_reboot", "mean"),
        median_reboot=("tot_reboot", "median"),
        mean_power_cycle=("tot_power_cycle", "mean"),
        mean_sw_reboot=("tot_sw_reboot", "mean"),
        mean_unknown=("tot_unknown", "mean"),
        mean_max_1h=("max_reboot_1h", "mean"),
    )

    by_outcome = df_stats.groupby("outcome").agg(
        n_visits=("visit_id", "count"),
        mean_reboot=("tot_reboot", "mean"),
        median_reboot=("tot_reboot", "median"),
        mean_power_cycle=("tot_power_cycle", "mean"),
        mean_sw_reboot=("tot_sw_reboot", "mean"),
        mean_unknown=("tot_unknown", "mean"),
        reboot_gt_10_pct=("tot_reboot", lambda x: float((x > 10).mean() * 100)),
    )

    by_parts = df_stats.groupby("parts_replaced", dropna=False).agg(
        n_visits=("visit_id", "count"),
        mean_reboot=("tot_reboot", "mean"),
        mean_power_cycle=("tot_power_cycle", "mean"),
        mean_sw_reboot=("tot_sw_reboot", "mean"),
        mean_unknown=("tot_unknown", "mean"),
    )

    # Effect size: Ratio between Fehler behoben and Kein Fehler gefunden
    mean_reboot_repaired = float(
        df_stats[df_stats["outcome"] == "Fehler behoben"]["tot_reboot"].mean()
    )
    mean_reboot_nofault = float(
        df_stats[df_stats["outcome"] == "Kein Fehler gefunden"]["tot_reboot"].mean()
    )
    mean_power_repaired = float(
        df_stats[df_stats["outcome"] == "Fehler behoben"]["tot_power_cycle"].mean()
    )
    mean_power_nofault = float(
        df_stats[df_stats["outcome"] == "Kein Fehler gefunden"]["tot_power_cycle"].mean()
    )

    return {
        "experiment_id": "E-04",
        "evaluable_visits": len(df_stats),
        "mean_reboot_repaired": mean_reboot_repaired,
        "mean_reboot_nofault": mean_reboot_nofault,
        "reboot_ratio_repaired_to_nofault": (
            mean_reboot_repaired / max(mean_reboot_nofault, 1e-4)
        ),
        "mean_power_cycle_repaired": mean_power_repaired,
        "mean_power_cycle_nofault": mean_power_nofault,
        "power_cycle_ratio_repaired_to_nofault": (
            mean_power_repaired / max(mean_power_nofault, 1e-4)
        ),
        "by_reason_table": by_reason,
        "by_outcome_table": by_outcome,
        "by_parts_table": by_parts,
    }


def run_experiment_e05(
    data_dir: Path | str | None = None,
    months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Experiment E-05: Radio Quality & CRC Noise Analysis.

    Analyzes LoRa packet volume, CRC error ratios, transmission success, and
    cellular signal quality conditioned on antenna type, site type, and installed meters.
    """
    months = months or DEFAULT_HISTORICAL_MONTHS
    gw = load_gateway_master(data_dir=data_dir, normalize_id="bare")
    mr = load_meter_read_success(data_dir=data_dir, normalize_id="bare")
    mr["week_start"] = pd.to_datetime(mr["week_start"]).dt.tz_localize("UTC")

    telem_dir = Path(data_dir) / "telemetry" if data_dir is not None else None
    telem = load_telemetry(
        telemetry_dir=telem_dir,
        months=months,
        columns=[
            "gateway_id",
            "ts_utc",
            "rx_nr_pkts",
            "rx_crc_bad",
            "tx_success",
            "rssi_good",
            "rssi_normal",
            "rssi_bad",
            "rscp_rsrp_good",
            "rscp_rsrp_normal",
            "rscp_rsrp_bad",
            "ecio_rsrq_good",
            "ecio_rsrq_normal",
            "ecio_rsrq_bad",
        ],
    )

    min_ts = telem["ts_utc"].min()
    max_ts = telem["ts_utc"].max()
    mr = mr[
        (mr["week_start"] >= min_ts)
        & (mr["week_start"] + pd.Timedelta(days=7) <= max_ts + pd.Timedelta(hours=1))
    ].copy()

    telem["week_start"] = telem["ts_utc"].dt.floor("D") - pd.to_timedelta(
        telem["ts_utc"].dt.dayofweek, unit="D"
    )
    telem_mr_weeks = telem[telem["week_start"].isin(mr["week_start"].unique())]

    rf_weekly = telem_mr_weeks.groupby(["gateway_id", "week_start"]).agg(
        tot_rx_pkts=("rx_nr_pkts", "sum"),
        tot_rx_crc_bad=("rx_crc_bad", "sum"),
        tot_tx_success=("tx_success", "sum"),
        mean_rssi_good=("rssi_good", "mean"),
        mean_rssi_normal=("rssi_normal", "mean"),
        mean_rssi_bad=("rssi_bad", "mean"),
        mean_rscp_good=("rscp_rsrp_good", "mean"),
        mean_rscp_normal=("rscp_rsrp_normal", "mean"),
        mean_rscp_bad=("rscp_rsrp_bad", "mean"),
        mean_ecio_good=("ecio_rsrq_good", "mean"),
        mean_ecio_bad=("ecio_rsrq_bad", "mean"),
    ).reset_index()

    rf_weekly["crc_ratio"] = rf_weekly["tot_rx_crc_bad"] / np.maximum(
        rf_weekly["tot_rx_pkts"], 1
    )

    rf_gw = pd.merge(
        rf_weekly,
        gw[["gateway_id", "antenna_type", "site_type", "n_meters_installed", "hw_model"]],
        on="gateway_id",
        how="left",
    )

    rf_full = pd.merge(
        rf_gw,
        mr[["gateway_id", "week_start", "meters_expected", "meters_read"]],
        on=["gateway_id", "week_start"],
        how="inner",
    )
    rf_full["read_ratio"] = rf_full["meters_read"] / rf_full["meters_expected"]
    rf_full["severe_deficit"] = (rf_full["read_ratio"] < 0.5).astype(int)

    by_antenna = rf_full.groupby("antenna_type").agg(
        n_weeks=("gateway_id", "count"),
        mean_meters=("n_meters_installed", "mean"),
        mean_rx_pkts=("tot_rx_pkts", "mean"),
        mean_crc_bad=("tot_rx_crc_bad", "mean"),
        mean_crc_ratio=("crc_ratio", "mean"),
        mean_rssi_bad=("mean_rssi_bad", "mean"),
        mean_read_ratio=("read_ratio", "mean"),
        severe_deficit_rate=("severe_deficit", "mean"),
    )

    by_site = rf_full.groupby("site_type").agg(
        n_weeks=("gateway_id", "count"),
        mean_meters=("n_meters_installed", "mean"),
        mean_rx_pkts=("tot_rx_pkts", "mean"),
        mean_crc_ratio=("crc_ratio", "mean"),
        mean_rssi_bad=("mean_rssi_bad", "mean"),
        mean_read_ratio=("read_ratio", "mean"),
        severe_deficit_rate=("severe_deficit", "mean"),
    )

    corr_cols = [
        "n_meters_installed",
        "tot_rx_pkts",
        "tot_rx_crc_bad",
        "crc_ratio",
        "tot_tx_success",
        "mean_rssi_bad",
        "mean_rscp_bad",
        "mean_ecio_bad",
        "read_ratio",
        "severe_deficit",
    ]
    corr_matrix = rf_full[corr_cols].corr()

    return {
        "experiment_id": "E-05",
        "total_evaluable_weeks": len(rf_full),
        "corr_rx_pkts_crc_bad": float(
            rf_full["tot_rx_pkts"].corr(rf_full["tot_rx_crc_bad"])
        ),
        "corr_crc_ratio_severe_deficit": float(
            rf_full["crc_ratio"].corr(rf_full["severe_deficit"])
        ),
        "corr_rssi_bad_severe_deficit": float(
            rf_full["mean_rssi_bad"].corr(rf_full["severe_deficit"])
        ),
        "corr_tx_success_read_ratio": float(
            rf_full["tot_tx_success"].corr(rf_full["read_ratio"])
        ),
        "by_antenna_table": by_antenna,
        "by_site_table": by_site,
        "correlation_matrix": corr_matrix,
    }


def run_stage3_cross_analysis(
    data_dir: Path | str | None = None,
    months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Cross-Analysis: Silence, Offline Duration, Reboots, and Lifecycle Cohorts."""
    months = months or DEFAULT_HISTORICAL_MONTHS
    gw = load_gateway_master(data_dir=data_dir, normalize_id="bare")
    mr = load_meter_read_success(data_dir=data_dir, normalize_id="bare")
    mr["week_start"] = pd.to_datetime(mr["week_start"]).dt.tz_localize("UTC")

    telem_dir = Path(data_dir) / "telemetry" if data_dir is not None else None
    telem = load_telemetry(
        telemetry_dir=telem_dir,
        months=months,
        columns=[
            "gateway_id",
            "ts_utc",
            "offline_duration_sec",
            "disconnection_cnt",
            "reboot_cnt",
            "r_cnt_power_cycle",
        ],
    )

    min_ts = telem["ts_utc"].min()
    max_ts = telem["ts_utc"].max()
    mr = mr[
        (mr["week_start"] >= min_ts)
        & (mr["week_start"] + pd.Timedelta(days=7) <= max_ts + pd.Timedelta(hours=1))
    ].copy()

    telem["week_start"] = telem["ts_utc"].dt.floor("D") - pd.to_timedelta(
        telem["ts_utc"].dt.dayofweek, unit="D"
    )
    telem_mr_weeks = telem[telem["week_start"].isin(mr["week_start"].unique())]

    agg = telem_mr_weeks.groupby(["gateway_id", "week_start"]).agg(
        n_telem_hours=("ts_utc", "count"),
        sum_offline_sec=("offline_duration_sec", "sum"),
        sum_disconnections=("disconnection_cnt", "sum"),
        sum_reboots=("reboot_cnt", "sum"),
        sum_power_cycles=("r_cnt_power_cycle", "sum"),
    ).reset_index()

    agg["missing_hours"] = 168 - agg["n_telem_hours"]

    corr_offline_missing = float(
        agg["sum_offline_sec"].corr(agg["missing_hours"])
    )
    corr_disc_missing = float(
        agg["sum_disconnections"].corr(agg["missing_hours"])
    )
    corr_reboots_disc = float(
        agg["sum_reboots"].corr(agg["sum_disconnections"])
    )
    corr_power_offline = float(
        agg["sum_power_cycles"].corr(agg["sum_offline_sec"])
    )
    corr_power_missing = float(
        agg["sum_power_cycles"].corr(agg["missing_hours"])
    )

    # Lifecycle cohorts
    gw_mr = pd.merge(
        mr,
        gw[["gateway_id", "installed_on", "decommissioned_on"]],
        on="gateway_id",
        how="left",
    )
    decom_gateways = int(
        gw_mr[gw_mr["decommissioned_on"].notna()]["gateway_id"].nunique()
    )

    return {
        "corr_offline_missing_hours": corr_offline_missing,
        "corr_disconnections_missing_hours": corr_disc_missing,
        "corr_reboots_disconnections": corr_reboots_disc,
        "corr_power_cycles_offline_sec": corr_power_offline,
        "corr_power_cycles_missing_hours": corr_power_missing,
        "decommissioned_gateways_count": decom_gateways,
    }
