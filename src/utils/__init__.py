"""Utility functions and centralized project configuration."""
from src.utils.config import (
    DATA_DIR,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
    TOTAL_SUBMISSION_ROWS,
    VISIT_COST_EUR,
    FAULT_COST_WEEKLY_EUR,
    MAX_REASON_CHARS,
    LATIN1_ENCODING,
    get_data_dir,
)
from src.utils.normalizer import (
    to_bare_hex,
    to_colon_hex,
    is_valid_gateway_id,
    normalize_series,
)

__all__ = [
    "DATA_DIR",
    "SCORED_WEEKS",
    "VISITS_PER_WEEK",
    "TOTAL_SUBMISSION_ROWS",
    "VISIT_COST_EUR",
    "FAULT_COST_WEEKLY_EUR",
    "MAX_REASON_CHARS",
    "LATIN1_ENCODING",
    "get_data_dir",
    "to_bare_hex",
    "to_colon_hex",
    "is_valid_gateway_id",
    "normalize_series",
]
