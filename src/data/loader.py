"""Data ingestion engine with Latin1 decoding, dynamic partition discovery, and UTC alignment.

Source Authority:
- [CONFIRMED BY LPDG - Data Dictionary & Brief]:
  CSVs use Latin1 encoding (German umlauts).
  telemetry is stored in partitioned Parquet format.
  ts_utc provides continuous UTC timestamps.
- [OBSERVED IN DATA]:
  gateway_master.csv: 332 rows, 11 cols (colon hex IDs).
  field_visits.csv: 642 rows, 8 cols (colon hex IDs).
  meter_read_success.csv: 7,226 rows, 4 cols (bare hex IDs).
  engineer_review_2026-02.xlsx: 120 rows, 6 cols (colon hex IDs).
  telemetry: 8 partitions (month=2025-08 to month=2026-03), 1,433,387 rows, 57 cols (bare hex IDs).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import pandas as pd

from src.utils.config import LATIN1_ENCODING, get_data_dir
from src.utils.normalizer import normalize_series

logger = logging.getLogger(__name__)


def load_gateway_master(
    data_dir: Path | str | None = None,
    parse_dates: bool = True,
    normalize_id: Literal["bare", "colon"] | None = None,
) -> pd.DataFrame:
    """Load gateway_master.csv.

    Args:
        data_dir: Path to directory containing the dataset files.
        parse_dates: Whether to parse installed_on, decommissioned_on, fw_updated_on as dates.
        normalize_id: Optional ID format normalization ('bare' or 'colon'). If None, preserves raw format.

    Returns:
        pd.DataFrame containing gateway master records (332 rows, 11 columns).
    """
    resolved_dir = get_data_dir(data_dir)
    file_path = resolved_dir / "gateway_master.csv"
    if not file_path.is_file():
        raise FileNotFoundError(f"gateway_master.csv not found at: {file_path}")

    df = pd.read_csv(file_path, encoding=LATIN1_ENCODING)

    if parse_dates:
        date_cols = ["installed_on", "decommissioned_on", "fw_updated_on"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if normalize_id is not None:
        df["gateway_id"] = normalize_series(df["gateway_id"], target_format=normalize_id)

    return df


def load_field_visits(
    data_dir: Path | str | None = None,
    parse_dates: bool = True,
    normalize_id: Literal["bare", "colon"] | None = None,
) -> pd.DataFrame:
    """Load field_visits.csv.

    Args:
        data_dir: Path to directory containing the dataset files.
        parse_dates: Whether to parse requested_on and visited_on as dates.
        normalize_id: Optional ID format normalization ('bare' or 'colon'). If None, preserves raw format.

    Returns:
        pd.DataFrame containing historical technician dispatch logs (642 rows, 8 columns).
    """
    resolved_dir = get_data_dir(data_dir)
    file_path = resolved_dir / "field_visits.csv"
    if not file_path.is_file():
        raise FileNotFoundError(f"field_visits.csv not found at: {file_path}")

    df = pd.read_csv(file_path, encoding=LATIN1_ENCODING)

    if parse_dates:
        date_cols = ["requested_on", "visited_on"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if normalize_id is not None:
        df["gateway_id"] = normalize_series(df["gateway_id"], target_format=normalize_id)

    return df


def load_meter_read_success(
    data_dir: Path | str | None = None,
    parse_dates: bool = True,
    normalize_id: Literal["bare", "colon"] | None = None,
) -> pd.DataFrame:
    """Load meter_read_success.csv.

    Args:
        data_dir: Path to directory containing the dataset files.
        parse_dates: Whether to parse week_start as dates.
        normalize_id: Optional ID format normalization ('bare' or 'colon'). If None, preserves raw format.

    Returns:
        pd.DataFrame containing weekly meter collection counts (7,226 rows, 4 columns).
    """
    resolved_dir = get_data_dir(data_dir)
    file_path = resolved_dir / "meter_read_success.csv"
    if not file_path.is_file():
        raise FileNotFoundError(f"meter_read_success.csv not found at: {file_path}")

    df = pd.read_csv(file_path, encoding=LATIN1_ENCODING)

    if parse_dates and "week_start" in df.columns:
        df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce")

    if normalize_id is not None:
        df["gateway_id"] = normalize_series(df["gateway_id"], target_format=normalize_id)

    return df


def load_engineer_review(
    data_dir: Path | str | None = None,
    parse_dates: bool = True,
    normalize_id: Literal["bare", "colon"] | None = None,
) -> pd.DataFrame:
    """Load engineer_review_2026-02.xlsx.

    Args:
        data_dir: Path to directory containing the dataset files.
        parse_dates: Whether to parse reviewed_on as dates.
        normalize_id: Optional ID format normalization ('bare' or 'colon'). If None, preserves raw format.

    Returns:
        pd.DataFrame containing engineer review audits (120 rows, 6 columns).
    """
    resolved_dir = get_data_dir(data_dir)
    file_path = resolved_dir / "engineer_review_2026-02.xlsx"
    if not file_path.is_file():
        raise FileNotFoundError(f"engineer_review_2026-02.xlsx not found at: {file_path}")

    df = pd.read_excel(file_path, engine="openpyxl")

    if parse_dates and "reviewed_on" in df.columns:
        df["reviewed_on"] = pd.to_datetime(df["reviewed_on"], errors="coerce")

    if normalize_id is not None:
        df["gateway_id"] = normalize_series(df["gateway_id"], target_format=normalize_id)

    return df


def discover_telemetry_partitions(telemetry_dir: Path | str | None = None) -> list[Path]:
    """Dynamically discover telemetry partition directories using filesystem globbing.

    Avoids hardcoding partition names or counts to support arbitrary unseen test partitions.

    Args:
        telemetry_dir: Path to telemetry directory. If None, resolves from default data directory.

    Returns:
        Sorted list of partition directory Paths (e.g. [Path('.../month=2025-08'), ...]).

    Raises:
        FileNotFoundError: If telemetry directory does not exist or has no partitions.
    """
    if telemetry_dir is None:
        resolved_data_dir = get_data_dir()
        base_dir = resolved_data_dir / "telemetry"
    else:
        base_dir = Path(telemetry_dir).resolve()
        if (base_dir / "telemetry").is_dir():
            base_dir = base_dir / "telemetry"

    if not base_dir.is_dir():
        raise FileNotFoundError(f"Telemetry directory does not exist at: {base_dir}")

    # Discover monthly partitions dynamically
    partitions = sorted(base_dir.glob("month=*"))
    if not partitions:
        # Fallback: check if the directory itself contains parquet files directly
        parquet_files = list(base_dir.glob("*.parquet"))
        if parquet_files:
            return [base_dir]
        raise FileNotFoundError(f"No telemetry partitions found matching 'month=*' in: {base_dir}")

    return partitions


def load_telemetry(
    telemetry_dir: Path | str | None = None,
    months: list[str] | None = None,
    columns: list[str] | None = None,
    parse_dates: bool = True,
    normalize_id: Literal["bare", "colon"] | None = None,
) -> pd.DataFrame:
    """Load telemetry data from dynamic monthly Parquet partitions.

    Aligns timestamps in continuous UTC via `ts_utc`, while preserving local `DateDt`
    and `hour` as reference columns.

    Args:
        telemetry_dir: Path to telemetry directory. If None, resolves dynamically.
        months: Optional list of month strings to filter (e.g. ['2025-08', '2025-09']).
        columns: Optional list of column names to load (loads all 57 columns if None).
        parse_dates: Whether to parse ts_utc as a continuous UTC datetime.
        normalize_id: Optional ID format normalization ('bare' or 'colon'). If None, preserves raw format.

    Returns:
        pd.DataFrame containing telemetry observations sorted by [gateway_id, ts_utc].
    """
    partitions = discover_telemetry_partitions(telemetry_dir)

    if months is not None:
        target_months = set(months)
        filtered = [
            p for p in partitions
            if any(m in p.name for m in target_months)
        ]
        if not filtered:
            available = [p.name for p in partitions]
            raise ValueError(
                f"None of requested months {months} found. Available partitions: {available}"
            )
        partitions = filtered

    frames: list[pd.DataFrame] = []
    for partition_path in partitions:
        part_df = pd.read_parquet(partition_path, columns=columns, engine="pyarrow")
        frames.append(part_df)

    if not frames:
        return pd.DataFrame(columns=columns or [])

    df = pd.concat(frames, ignore_index=True)

    if parse_dates and "ts_utc" in df.columns:
        # Guarantee continuous UTC parsing without local DST daylight shifts
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)

    if normalize_id is not None and "gateway_id" in df.columns:
        df["gateway_id"] = normalize_series(df["gateway_id"], target_format=normalize_id)

    # Sort deterministically by gateway_id and ts_utc if present
    sort_cols = [c for c in ["gateway_id", "ts_utc"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ignore_index=True)

    return df
