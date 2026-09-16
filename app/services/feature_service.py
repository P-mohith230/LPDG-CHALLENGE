"""Service managing feature definitions, invariants, and failure signatures.

Directly imports and reflects authoritative definitions from:
- src.features.builder (29 baseline features)
- src.features.gateway_baseline (3 gateway self-baseline features)
- src.intelligence.failure_signatures (5 failure signatures in SIGNATURE_REGISTRY)
"""

from __future__ import annotations

from src.features.builder import get_feature_family_columns
from src.intelligence.failure_signatures import SIGNATURE_REGISTRY, SignatureDefinition

# Gateway self-baseline features explicitly defined in C3 architecture
GATEWAY_BASELINE_FEATURES = [
    "feat_gw_z_offline",
    "feat_gw_z_missing",
    "feat_gw_relative_anomaly_score",
]

# Physical Domain Invariants
PHYSICAL_INVARIANTS = {
    "wall_clock_peak_offline": "min(168.0, max(offline_duration_sec) / 3600.0) — eliminates impossible durations (>168h/wk) caused by frozen register snapshots.",
    "hourly_conservation": "feat_observed_hours + feat_missing_hours == 168.0 — enforces distinct hourly floor bucketing across packet burst gateways.",
    "self_baseline_cold_start": "Fall back to fleet medians if gateway operating history < 72h (4.30% prevalence).",
}


class FeatureService:
    """Read-only service for C3 production features and failure signatures."""

    @staticmethod
    def get_baseline_feature_families() -> dict[str, list[str]]:
        """Retrieve the 29 baseline features grouped into 4 distinct families."""
        families = get_feature_family_columns()
        # Exclude the synthetic 'all' union key to return distinct families
        return {k: v for k, v in families.items() if k != "all"}

    @staticmethod
    def get_gateway_baseline_features() -> list[str]:
        """Retrieve the 3 gateway self-baseline features."""
        return list(GATEWAY_BASELINE_FEATURES)

    @classmethod
    def get_all_c3_features(cls) -> list[str]:
        """Return the complete list of exactly 32 C3 production features."""
        families = cls.get_baseline_feature_families()
        baseline_feats = []
        for cols in families.values():
            baseline_feats.extend(cols)
        return baseline_feats + cls.get_gateway_baseline_features()

    @classmethod
    def get_feature_counts(cls) -> dict[str, int]:
        """Return feature counts by category."""
        families = cls.get_baseline_feature_families()
        counts = {fam: len(cols) for fam, cols in families.items()}
        counts["gateway_self_baselines"] = len(cls.get_gateway_baseline_features())
        counts["total_c3_features"] = len(cls.get_all_c3_features())
        return counts

    @staticmethod
    def get_failure_signatures() -> list[SignatureDefinition]:
        """Return the authoritative failure signatures from SIGNATURE_REGISTRY."""
        return list(SIGNATURE_REGISTRY)

    @staticmethod
    def get_physical_invariants() -> dict[str, str]:
        """Return the grounded physical invariants."""
        return dict(PHYSICAL_INVARIANTS)
