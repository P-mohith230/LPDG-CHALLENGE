"""Centralized project configuration and directory path resolver.

Classification of parameters:
- SCORED_WEEKS, VISITS_PER_WEEK, TOTAL_SUBMISSION_ROWS, VISIT_COST_EUR,
  FAULT_COST_WEEKLY_EUR, MAX_REASON_CHARS: [CONFIRMED BY LPDG]
- Directory search order and environment variables: [CANDIDATE DECISION — INTERNAL]
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

# Project root directory (resolved dynamically from file location)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Official LPDG Competition Parameters [CONFIRMED BY LPDG - Brief p. 2, FAQ R1 §5.1, FAQ R2 §4.1]
SCORED_WEEKS: list[dt.date] = [
    dt.date(2026, 2, 2) + dt.timedelta(days=7 * i) for i in range(8)
]
VISITS_PER_WEEK: int = 15
TOTAL_SUBMISSION_ROWS: int = len(SCORED_WEEKS) * VISITS_PER_WEEK  # Exactly 120 rows
VISIT_COST_EUR: float = 380.0
FAULT_COST_WEEKLY_EUR: float = 600.0
COST_PER_VISIT: float = VISIT_COST_EUR
COST_PER_UNVISITED_FAULT_WEEK: float = FAULT_COST_WEEKLY_EUR
TOTAL_FIXED_VISIT_BUDGET_EUR: float = TOTAL_SUBMISSION_ROWS * VISIT_COST_EUR  # €45,600
MAX_REASON_CHARS: int = 300
REQUIRED_SUBMISSION_COLUMNS: list[str] = [
    "week_start",
    "rank",
    "gateway_id",
    "score",
    "reason",
]

# Encodings & Timezones [CONFIRMED BY LPDG - Data Dictionary & validate_submission.py]
LATIN1_ENCODING: str = "latin1"
UTC_TIMEZONE: str = "UTC"
LOCAL_TIMEZONE: str = "Europe/Berlin"


def get_data_dir(custom_path: Path | str | None = None) -> Path:
    """Resolve the raw challenge data directory.

    Resolution order:
    1. Explicit custom_path argument (if provided and exists).
    2. Environment variable LPDG_DATA_DIR (if set and exists).
    3. PROJECT_ROOT / 'data'
    4. PROJECT_ROOT / 'OneDrive_2026-08-31' / 'Innovation Hub 2026' / '03-challenge-data' / 'data'

    Raises:
        FileNotFoundError: If no valid data directory is found.
    """
    candidates: list[Path] = []

    if custom_path is not None:
        candidates.append(Path(custom_path).resolve())

    env_dir = os.environ.get("LPDG_DATA_DIR")
    if env_dir:
        candidates.append(Path(env_dir).resolve())

    candidates.append(PROJECT_ROOT / "data")
    candidates.append(
        PROJECT_ROOT
        / "OneDrive_2026-08-31"
        / "Innovation Hub 2026"
        / "03-challenge-data"
        / "data"
    )

    for candidate in candidates:
        if candidate.is_dir() and (candidate / "gateway_master.csv").is_file():
            return candidate

    searched_paths = "\n - ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Could not find valid LPDG challenge data directory. Looked in:\n - {searched_paths}\n"
        f"Please provide a valid path or set the LPDG_DATA_DIR environment variable."
    )


# Default resolved data directory for convenient import
try:
    DATA_DIR: Path = get_data_dir()
except FileNotFoundError:
    DATA_DIR = PROJECT_ROOT / "data"
