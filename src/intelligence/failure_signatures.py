"""Innovation 2: Interpretable Failure Signature Engine.

Source Authority & Method:
- Operates as an independent, transparent rule-based evidence layer.
- Evaluates operational degradation signatures from multi-signal telemetry patterns.
- Does NOT assert ground truth physical defects; provides evidence-based signature indicators.
- Outputs individual signature triggers, a composite signature evidence score [0.0, 1.0],
  and human-readable diagnostic tags for reason generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SignatureDefinition:
    """Metadata and definition of a candidate failure signature."""

    signature_id: str
    name: str
    family: str
    description: str
    weight: float


# The 6 Grounded Telemetry Failure Signatures
SIGNATURE_REGISTRY: list[SignatureDefinition] = [
    SignatureDefinition(
        signature_id="SIG_01_CONNECTIVITY_COLLAPSE",
        name="Cellular Backhaul Outage with Disconnection Burden",
        family="connectivity",
        description="Peak offline duration >= 24h combined with disconnection count >= 5 and missingness >= 12h.",
        weight=0.25,
    ),
    SignatureDefinition(
        signature_id="SIG_02_HARDWARE_POWER_CYCLE_SURGE",
        name="Hardware Power-Cycle Instability",
        family="stability",
        description="Power cycle in trailing 24h >= 1, or weekly power cycles >= 3, with total reboots >= 5.",
        weight=0.20,
    ),
    SignatureDefinition(
        signature_id="SIG_03_PERSISTENT_SILENCE_BLACKOUT",
        name="Persistent Telemetry Silence / Communications Blackout",
        family="availability",
        description="Tail silence adjacent to cutoff >= 24h or weekly missing hours >= 48h.",
        weight=0.25,
    ),
    SignatureDefinition(
        signature_id="SIG_04_RADIO_DOWNLINK_DEGRADATION",
        name="Radio Front-End / Downlink Degradation",
        family="radio",
        description="Bad RSSI packet rate >= 2.0/h and CPU load >= 1.5, with low TX success.",
        weight=0.10,
    ),
    SignatureDefinition(
        signature_id="SIG_05_MULTI_DOMAIN_CRISIS",
        name="Multi-Domain Compounded Failure State",
        family="composite",
        description="Simultaneous degradation in backhaul (offline >= 12h), availability (missing >= 24h), and stability (reboots >= 5).",
        weight=0.20,
    ),
]


def evaluate_failure_signatures(features_df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate all registered failure signatures on engineered feature vectors.

    Args:
        features_df: DataFrame containing the 31 engineered features.

    Returns:
        pd.DataFrame containing original keys plus:
        - sig_01_connectivity_collapse: int (0 or 1)
        - sig_02_hardware_power_cycle_surge: int (0 or 1)
        - sig_03_persistent_silence_blackout: int (0 or 1)
        - sig_04_radio_downlink_degradation: int (0 or 1)
        - sig_05_multi_domain_crisis: int (0 or 1)
        - sig_active_count: int (total triggered signatures)
        - feat_signature_score: float in [0.0, 1.0] (weighted evidence score)
        - sig_diagnostic_tags: str (semicolon-separated diagnostic tags)
    """
    df = features_df.copy()

    # Feature inputs with safe defaults
    offline_hrs = df.get("feat_offline_hours", pd.Series(0.0, index=df.index)).fillna(0.0)
    disconns = df.get("feat_sum_disconnections", pd.Series(0, index=df.index)).fillna(0)
    missing_hrs = df.get("feat_missing_hours", pd.Series(0, index=df.index)).fillna(0)
    tail_silence = df.get("feat_tail_silence", pd.Series(0, index=df.index)).fillna(0)
    power_recent = df.get("feat_power_cycle_recent_24h", pd.Series(0, index=df.index)).fillna(0)
    power_cycles = df.get("feat_power_cycle_cnt", pd.Series(0, index=df.index)).fillna(0)
    reboots = df.get("feat_reboot_cnt_total", pd.Series(0, index=df.index)).fillna(0)
    rssi_bad = df.get("feat_mean_rssi_bad", pd.Series(0.0, index=df.index)).fillna(0.0)
    load1 = df.get("feat_mean_load1", pd.Series(0.0, index=df.index)).fillna(0.0)
    tx_success = df.get("feat_tot_tx_success", pd.Series(0, index=df.index)).fillna(0)

    # Signature 1: Cellular Backhaul Outage with Disconnection Burden
    sig_1 = (
        (offline_hrs >= 24.0) & (disconns >= 5) & (missing_hrs >= 12)
    ).astype(int)

    # Signature 2: Hardware Power-Cycle Instability
    sig_2 = (
        ((power_recent >= 1) | (power_cycles >= 3)) & (reboots >= 5)
    ).astype(int)

    # Signature 3: Persistent Telemetry Silence / Communications Blackout
    sig_3 = (
        (tail_silence >= 24) | (missing_hrs >= 48)
    ).astype(int)

    # Signature 4: Radio Front-End / Downlink Degradation
    sig_4 = (
        (rssi_bad >= 2.0) & (load1 >= 1.5) & (tx_success < 50)
    ).astype(int)

    # Signature 5: Multi-Domain Compounded Failure State (At least 3 simultaneous domains)
    domain_backhaul = (offline_hrs >= 12.0) | (disconns >= 10)
    domain_avail = (missing_hrs >= 24) | (tail_silence >= 12)
    domain_stability = (power_cycles >= 2) | (reboots >= 5)
    sig_5 = (
        domain_backhaul.astype(int) + domain_avail.astype(int) + domain_stability.astype(int) >= 3
    ).astype(int)

    # Output columns
    out_df = pd.DataFrame(index=df.index)
    if "gateway_id" in df.columns:
        out_df["gateway_id"] = df["gateway_id"]
    if "decision_week" in df.columns:
        out_df["decision_week"] = df["decision_week"]

    out_df["sig_01_connectivity_collapse"] = sig_1
    out_df["sig_02_hardware_power_cycle_surge"] = sig_2
    out_df["sig_03_persistent_silence_blackout"] = sig_3
    out_df["sig_04_radio_downlink_degradation"] = sig_4
    out_df["sig_05_multi_domain_crisis"] = sig_5

    active_count = sig_1 + sig_2 + sig_3 + sig_4 + sig_5
    out_df["sig_active_count"] = active_count

    # Weighted Composite Signature Score [0.0, 1.0]
    raw_sig_score = (
        0.25 * sig_1
        + 0.20 * sig_2
        + 0.25 * sig_3
        + 0.10 * sig_4
        + 0.20 * sig_5
    )
    out_df["feat_signature_score"] = np.clip(raw_sig_score, 0.0, 1.0)

    # Generate diagnostic tags for reason generator
    def build_tags(row: pd.Series) -> str:
        tags = []
        if row["sig_01_connectivity_collapse"] == 1:
            tags.append("Backhaul Outage Pattern")
        if row["sig_02_hardware_power_cycle_surge"] == 1:
            tags.append("Power-Cycle Instability")
        if row["sig_03_persistent_silence_blackout"] == 1:
            tags.append("Prolonged Telemetry Blackout")
        if row["sig_04_radio_downlink_degradation"] == 1:
            tags.append("Radio Front-End Degradation")
        if row["sig_05_multi_domain_crisis"] == 1:
            tags.append("Multi-Domain Telemetry Crisis")
        return "; ".join(tags) if tags else "None"

    out_df["sig_diagnostic_tags"] = out_df.apply(build_tags, axis=1)

    return out_df


def get_signature_feature_columns() -> list[str]:
    """Return the list of signature feature columns suitable for model inputs."""
    return [
        "sig_01_connectivity_collapse",
        "sig_02_hardware_power_cycle_surge",
        "sig_03_persistent_silence_blackout",
        "sig_04_radio_downlink_degradation",
        "sig_05_multi_domain_crisis",
        "sig_active_count",
        "feat_signature_score",
    ]
