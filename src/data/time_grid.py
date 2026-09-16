"""Continuous UTC time-grid alignment and missing telemetry (omitted rows) detection.

Source Authority:
- [CONFIRMED BY LPDG - FAQ R2 §3.2, §8.1]:
  Telemetry observations are hourly. Silence (omitted rows) is a physical phenomenon
  where gateways cease transmitting; absent hours indicate potential power loss,
  backhaul network failure, or firmware crash.
- [OBSERVED IN DATA]:
  Telemetry Parquet files omit silent hours entirely rather than storing NaN rows.
  Time-grid alignment is necessary to expose silence spells and prevent time-compression
  in rolling window aggregations.
"""

from __future__ import annotations

from typing import Sequence
import numpy as np
import pandas as pd


def build_hourly_grid(
    gateway_ids: Sequence[str] | pd.Series,
    start_utc: pd.Timestamp | str,
    end_utc: pd.Timestamp | str,
    freq: str = "1h",
) -> pd.DataFrame:
    """Construct a complete regular hourly UTC grid across all specified gateways.

    Args:
        gateway_ids: Collection of gateway IDs (should be normalized consistently).
        start_utc: Grid start timestamp (UTC).
        end_utc: Grid end timestamp (UTC).
        freq: Frequency string, defaults to '1h'.

    Returns:
        pd.DataFrame with columns ['gateway_id', 'ts_utc'] representing the complete
        Cartesian product of all gateways and continuous hourly timestamps.
    """
    unique_ids = sorted(set(gateway_ids))
    if not unique_ids:
        return pd.DataFrame(columns=["gateway_id", "ts_utc"])

    # Ensure UTC-aware timestamps
    start_ts = pd.to_datetime(start_utc, utc=True)
    end_ts = pd.to_datetime(end_utc, utc=True)

    if start_ts > end_ts:
        raise ValueError(f"start_utc ({start_ts}) cannot be after end_utc ({end_ts})")

    timestamps = pd.date_range(start=start_ts, end=end_ts, freq=freq, tz="UTC")

    # MultiIndex Cartesian product
    multi_idx = pd.MultiIndex.from_product(
        [unique_ids, timestamps],
        names=["gateway_id", "ts_utc"],
    )

    grid_df = multi_idx.to_frame(index=False)
    return grid_df


def find_missing_hours(
    telemetry_df: pd.DataFrame,
    gateway_ids: Sequence[str] | None = None,
    start_utc: pd.Timestamp | str | None = None,
    end_utc: pd.Timestamp | str | None = None,
    id_col: str = "gateway_id",
    time_col: str = "ts_utc",
) -> pd.DataFrame:
    """Identify absent (omitted) hours in telemetry data for each gateway.

    Args:
        telemetry_df: DataFrame containing telemetry records.
        gateway_ids: Optional list of gateways to evaluate. Defaults to gateways in telemetry_df.
        start_utc: Grid start time. Defaults to min(ts_utc) in telemetry_df.
        end_utc: Grid end time. Defaults to max(ts_utc) in telemetry_df.
        id_col: Name of gateway identifier column.
        time_col: Name of timestamp column.

    Returns:
        pd.DataFrame of omitted (gateway_id, ts_utc) rows sorted by gateway and time.
    """
    if telemetry_df.empty and (not gateway_ids or start_utc is None or end_utc is None):
        return pd.DataFrame(columns=[id_col, time_col])

    # Standardize timestamps in telemetry
    t_df = telemetry_df[[id_col, time_col]].copy()
    t_df[time_col] = pd.to_datetime(t_df[time_col], utc=True)

    target_ids = gateway_ids if gateway_ids is not None else t_df[id_col].unique()
    grid_start = start_utc if start_utc is not None else t_df[time_col].min()
    grid_end = end_utc if end_utc is not None else t_df[time_col].max()

    full_grid = build_hourly_grid(target_ids, grid_start, grid_end)

    # Set indicator to find set difference
    merged = pd.merge(
        full_grid,
        t_df,
        on=[id_col, time_col],
        how="left",
        indicator=True,
    )

    missing = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
    return missing.sort_values([id_col, time_col], ignore_index=True)


def align_telemetry_to_grid(
    telemetry_df: pd.DataFrame,
    gateway_ids: Sequence[str] | None = None,
    start_utc: pd.Timestamp | str | None = None,
    end_utc: pd.Timestamp | str | None = None,
    id_col: str = "gateway_id",
    time_col: str = "ts_utc",
) -> pd.DataFrame:
    """Align telemetry records to a complete regular hourly grid, filling omitted rows.

    Adds an `is_omitted` boolean column (True for synthetic filled hours, False for observed).

    Args:
        telemetry_df: Telemetry DataFrame.
        gateway_ids: Optional collection of gateway IDs.
        start_utc: Grid start UTC timestamp.
        end_utc: Grid end UTC timestamp.
        id_col: Gateway ID column name.
        time_col: Timestamp column name.

    Returns:
        Regular hourly pd.DataFrame with NaN for unobserved measurements and `is_omitted` flag.
    """
    if telemetry_df.empty:
        if gateway_ids and start_utc and end_utc:
            grid = build_hourly_grid(gateway_ids, start_utc, end_utc)
            grid["is_omitted"] = True
            return grid
        return telemetry_df.copy()

    t_df = telemetry_df.copy()
    t_df[time_col] = pd.to_datetime(t_df[time_col], utc=True)

    target_ids = gateway_ids if gateway_ids is not None else t_df[id_col].unique()
    grid_start = start_utc if start_utc is not None else t_df[time_col].min()
    grid_end = end_utc if end_utc is not None else t_df[time_col].max()

    full_grid = build_hourly_grid(target_ids, grid_start, grid_end)

    aligned = pd.merge(
        full_grid,
        t_df,
        on=[id_col, time_col],
        how="left",
        indicator=True,
    )

    aligned["is_omitted"] = aligned["_merge"] == "left_only"
    aligned = aligned.drop(columns=["_merge"])
    return aligned.sort_values([id_col, time_col], ignore_index=True)


def compute_silence_spells(
    telemetry_df: pd.DataFrame,
    gateway_ids: Sequence[str] | None = None,
    start_utc: pd.Timestamp | str | None = None,
    end_utc: pd.Timestamp | str | None = None,
    id_col: str = "gateway_id",
    time_col: str = "ts_utc",
) -> pd.DataFrame:
    """Compute silence statistics per gateway over the specified time window.

    Metrics computed:
    - total_expected_hours: Total hours in the continuous grid.
    - observed_hours: Count of received telemetry rows.
    - missing_hours: Count of omitted telemetry rows.
    - missing_pct: Percentage of expected hours missing.
    - max_consecutive_silence_hours: Longest consecutive omitted hour streak.
    - current_silence_streak_hours: Unbroken omitted hour streak leading to the end of the window.

    Returns:
        pd.DataFrame indexed by gateway_id with silence metric columns.
    """
    aligned = align_telemetry_to_grid(
        telemetry_df,
        gateway_ids=gateway_ids,
        start_utc=start_utc,
        end_utc=end_utc,
        id_col=id_col,
        time_col=time_col,
    )

    if aligned.empty:
        return pd.DataFrame(
            columns=[
                "gateway_id",
                "total_expected_hours",
                "observed_hours",
                "missing_hours",
                "missing_pct",
                "max_consecutive_silence_hours",
                "current_silence_streak_hours",
            ]
        )

    records: list[dict] = []
    for gid, group in aligned.groupby(id_col):
        is_omitted = group["is_omitted"].to_numpy(dtype=bool)
        total_exp = len(is_omitted)
        missing_cnt = int(np.sum(is_omitted))
        obs_cnt = total_exp - missing_cnt
        missing_pct = (missing_cnt / total_exp * 100.0) if total_exp > 0 else 0.0

        # Compute max consecutive streak of True values
        max_streak = 0
        current_streak = 0
        for val in is_omitted:
            if val:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
            else:
                current_streak = 0

        # Compute tail streak (consecutive missing at the end of the window)
        tail_streak = 0
        for val in reversed(is_omitted):
            if val:
                tail_streak += 1
            else:
                break

        records.append(
            {
                "gateway_id": gid,
                "total_expected_hours": total_exp,
                "observed_hours": obs_cnt,
                "missing_hours": missing_cnt,
                "missing_pct": round(missing_pct, 2),
                "max_consecutive_silence_hours": max_streak,
                "current_silence_streak_hours": tail_streak,
            }
        )

    return pd.DataFrame(records)
