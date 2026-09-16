"""Bidirectional gateway ID normalizer and format validator.

Source authority:
- [CONFIRMED BY LPDG - validate_submission.py]:
  Accepts either 12-char bare hex (e.g. '0639EA5602C1') or 17-char colon-separated
  hex (e.g. '06:39:EA:56:02:C1'). Both formats represent the same gateway MAC address.
- [OBSERVED IN DATA]:
  gateway_master, field_visits, and engineer_review use 17-char colon hex.
  telemetry and meter_read_success use 12-char bare hex.
"""

from __future__ import annotations

import re
from typing import Literal
import pandas as pd

_BARE_PATTERN = re.compile(r"^[0-9A-Fa-f]{12}$")
_COLON_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def is_valid_gateway_id(value: str) -> bool:
    """Check if a string is a valid gateway ID in either bare or colon hex format.

    Args:
        value: Candidate gateway ID string.

    Returns:
        True if value matches 12-char bare hex or 17-char colon hex, False otherwise.
    """
    if not isinstance(value, str):
        return False
    text = value.strip()
    return bool(_BARE_PATTERN.match(text) or _COLON_PATTERN.match(text))


def to_bare_hex(value: str) -> str:
    """Normalize a gateway ID into a 12-character uppercase bare hexadecimal string.

    Example:
        '06:39:ea:56:02:c1' -> '0639EA5602C1'
        '0639ea5602c1'       -> '0639EA5602C1'

    Args:
        value: Gateway ID in bare or colon hex format.

    Returns:
        12-character uppercase hexadecimal string.

    Raises:
        ValueError: If value is not a valid bare or colon gateway ID.
    """
    if not isinstance(value, str):
        raise TypeError(f"Gateway ID must be a string, got {type(value).__name__}: {value!r}")
    text = value.strip()
    if _BARE_PATTERN.match(text):
        return text.upper()
    if _COLON_PATTERN.match(text):
        return text.replace(":", "").upper()
    raise ValueError(
        f"Invalid gateway ID format: {value!r}. "
        "Expected 12 hex characters (e.g. '0639EA5602C1') or "
        "17 colon-separated hex characters (e.g. '06:39:EA:56:02:C1')."
    )


def to_colon_hex(value: str) -> str:
    """Normalize a gateway ID into a 17-character uppercase colon-delimited hexadecimal string.

    Example:
        '0639ea5602c1'       -> '06:39:EA:56:02:C1'
        '06:39:ea:56:02:c1' -> '06:39:EA:56:02:C1'

    Args:
        value: Gateway ID in bare or colon hex format.

    Returns:
        17-character uppercase colon-delimited hexadecimal string.

    Raises:
        ValueError: If value is not a valid bare or colon gateway ID.
    """
    if not isinstance(value, str):
        raise TypeError(f"Gateway ID must be a string, got {type(value).__name__}: {value!r}")
    text = value.strip()
    if _COLON_PATTERN.match(text):
        return text.upper()
    if _BARE_PATTERN.match(text):
        upper_bare = text.upper()
        return ":".join(upper_bare[i : i + 2] for i in range(0, 12, 2))
    raise ValueError(
        f"Invalid gateway ID format: {value!r}. "
        "Expected 12 hex characters (e.g. '0639EA5602C1') or "
        "17 colon-separated hex characters (e.g. '06:39:EA:56:02:C1')."
    )


def normalize_series(
    series: pd.Series,
    target_format: Literal["bare", "colon"] = "bare",
) -> pd.Series:
    """Normalize an entire pandas Series of gateway IDs to the desired format.

    Args:
        series: Pandas Series containing gateway IDs.
        target_format: 'bare' for 12-char hex, 'colon' for 17-char colon-delimited hex.

    Returns:
        Pandas Series with normalized IDs.

    Raises:
        ValueError: If target_format is invalid or if any element cannot be normalized.
    """
    if target_format == "bare":
        converter = to_bare_hex
    elif target_format == "colon":
        converter = to_colon_hex
    else:
        raise ValueError(
            f"Invalid target_format: {target_format!r}. Must be 'bare' or 'colon'."
        )

    return series.apply(converter)
