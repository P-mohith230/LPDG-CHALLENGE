"""Evidence-Based Reason Generator for Technician Dispatch Recommendations.

Source Authority:
- Section 30 [REASON GENERATION]:
  Length strictly <= 300 characters.
  Deterministic, human-readable, evidence-based.
  Grounds every statement strictly in pre-decision boundary telemetry and asset metadata.
  No fabricated causes or speculative language.
"""

from __future__ import annotations

import logging
from typing import Any
import pandas as pd

logger = logging.getLogger(__name__)

MAX_REASON_CHARS = 300


def build_dispatch_reason(
    row: dict[str, Any] | pd.Series,
    max_length: int = MAX_REASON_CHARS,
) -> str:
    """Construct an evidence-grounded dispatch rationale string strictly within max_length.

    Evaluates:
    1. Telemetry silence & missingness (tail silence, missing ratio).
    2. Cellular backhaul offline duration & disconnection count.
    3. Hardware stability (power cycles, reboots).
    4. Asset context (connected meters, site/antenna context).

    Args:
        row: Series or dict containing engineered feature values and risk score.
        max_length: Strict character limit (default: 300).

    Returns:
        Deterministic, concise rationale string (<= max_length chars).
    """
    clauses: list[str] = []

    # 1. Telemetry silence clause
    tail_silence = int(row.get("feat_tail_silence", 0))
    missing_hrs = int(row.get("feat_missing_hours", 0))
    if tail_silence >= 24:
        clauses.append(f"Severe telemetry blackout ({tail_silence}h trailing silence)")
    elif tail_silence >= 4:
        clauses.append(f"Recent transmission gap ({tail_silence}h tail silence)")
    elif missing_hrs >= 24:
        clauses.append(f"High missingness ({missing_hrs}h unobserved in trailing week)")

    # 2. Cellular / Backhaul offline clause
    offline_hrs = float(row.get("feat_offline_hours", 0.0))
    disconns = int(row.get("feat_sum_disconnections", 0))
    if offline_hrs >= 24.0:
        clauses.append(f"severe reported backhaul outage signal (peak {offline_hrs:.1f}h event)")
    elif offline_hrs >= 4.0:
        clauses.append(f"elevated reported offline duration (peak {offline_hrs:.1f}h event)")
    elif disconns >= 10:
        clauses.append(f"frequent backhaul disconnection activity ({disconns} peak events)")

    # 3. Hardware / Power cycle clause
    power_cycles = int(row.get("feat_power_cycle_cnt", 0))
    power_recent = int(row.get("feat_power_cycle_recent_24h", 0))
    reboots = int(row.get("feat_reboot_cnt_total", 0))
    if power_recent >= 1:
        clauses.append(f"power-cycle reboot in past 24h ({power_recent} event)")
    elif power_cycles >= 2:
        clauses.append(f"repeated power-cycle activity ({power_cycles} events)")
    elif reboots >= 5:
        clauses.append(f"unstable system reboots ({reboots} restarts)")

    # 4. Connected meters context clause
    n_meters = int(row.get("feat_n_meters_installed", 0))
    context_str = f" [high-impact hub: {n_meters} meters]" if n_meters >= 300 else ""

    # 5. Diagnostic signature clause
    sig_tag = str(row.get("sig_diagnostic_tags", "")).strip()
    sig_str = f" [{sig_tag}]" if sig_tag and sig_tag != "nan" else ""

    # Fallback if no specific threshold triggered
    if not clauses:
        risk = float(row.get("risk_score", 0.0))
        reason = f"Elevated multivariate failure risk (score: {risk:.2f}) across telemetry signals{context_str}{sig_str}."
    else:
        # Join clauses
        first = clauses[0][0].upper() + clauses[0][1:]
        rest = ", ".join(clauses[1:])
        if rest:
            reason = f"{first} with {rest}{context_str}{sig_str}."
        else:
            reason = f"{first}{context_str}{sig_str}."

    # Enforce strict length constraint
    if len(reason) > max_length:
        reason = reason[: max_length - 3] + "..."

    return reason

