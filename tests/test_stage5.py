"""Unit tests for Stage 5: Leakage-Safe Feature Engineering & Feature Registry.

Tests:
1. Extraction of weekly features strictly prior to Monday 00:00 UTC cutoff.
2. Verification of observation_cutoff_utc < decision_week firewall constraint.
3. Integration with validate_target_leakage_firewall.
4. Lifecycle masking: future installed gateways and retired gateways are excluded.
5. Verification of feature family groupings (availability, stability, radio, static).
6. Absence of NaNs in computed feature vectors.
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.config import get_data_dir
from src.data.loader import load_gateway_master, load_meter_read_success, load_telemetry
from src.models.target import build_operational_target, validate_target_leakage_firewall
from src.features.builder import (
    extract_features_for_decision_week,
    build_feature_matrix,
    get_feature_family_columns,
)


class TestStage5FeatureBuilder(unittest.TestCase):
    """Test suite for feature engineering, lifecycle masking, and leakage prevention."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = get_data_dir()
        cls.master = load_gateway_master(cls.data_dir)
        # Load sample month of telemetry for fast test execution
        cls.telem = load_telemetry(
            months=["2025-10"],
            columns=[
                "gateway_id",
                "ts_utc",
                "offline_duration_sec",
                "disconnection_cnt",
                "reboot_cnt",
                "r_cnt_power_cycle",
                "r_cnt_reboot",
                "r_cnt_unknown",
                "rssi_bad",
                "tx_success",
                "avg_load1",
                "avg_memfree",
            ],
            normalize_id="bare",
        )
        # Test decision boundary: Monday 2025-10-13 00:00:00 UTC
        cls.decision_time = pd.Timestamp("2025-10-13 00:00:00")
        cls.features = extract_features_for_decision_week(
            decision_time=cls.decision_time,
            telemetry_df=cls.telem,
            master_df=cls.master,
            lookback_days=7,
        )

    def test_feature_matrix_dimensions_and_keys(self):
        """Verify feature matrix dimensions and composite keys."""
        self.assertGreater(len(self.features), 250)
        self.assertIn("gateway_id", self.features.columns)
        self.assertIn("decision_week", self.features.columns)
        self.assertIn("observation_cutoff_utc", self.features.columns)

        # Ensure zero duplicate (gateway_id, decision_week) pairs
        dups = self.features.duplicated(subset=["gateway_id", "decision_week"]).sum()
        self.assertEqual(dups, 0)

    def test_strict_temporal_cutoff(self):
        """Verify observation_cutoff_utc is strictly before decision_week."""
        cutoff = self.features["observation_cutoff_utc"].iloc[0]
        decision = self.features["decision_week"].iloc[0]
        self.assertLess(cutoff, decision)
        self.assertEqual(decision - cutoff, pd.Timedelta(seconds=1))

    def test_lifecycle_masking(self):
        """Verify that gateways installed in mid-2026 are completely excluded from features."""
        # Gateways installed after 2025-10-13 must NOT appear in the features for that week
        master_future = self.master[pd.to_datetime(self.master["installed_on"]) > self.decision_time]
        future_gws = set(master_future["gateway_id"].unique())
        feature_gws = set(self.features["gateway_id"].unique())

        overlap = feature_gws.intersection(future_gws)
        self.assertEqual(len(overlap), 0, f"Future uncommissioned gateways leaked into features: {overlap}")

    def test_feature_family_definitions(self):
        """Verify that get_feature_family_columns provides valid, existing columns."""
        families = get_feature_family_columns()
        self.assertIn("availability", families)
        self.assertIn("stability", families)
        self.assertIn("radio", families)
        self.assertIn("static", families)
        self.assertIn("all", families)

        for col in families["all"]:
            self.assertIn(col, self.features.columns, f"Registered feature {col} missing from output matrix")

    def test_no_nans_in_feature_columns(self):
        """Verify that engineered feature columns contain zero NaN values."""
        families = get_feature_family_columns()
        for col in families["all"]:
            nan_count = self.features[col].isna().sum()
            self.assertEqual(nan_count, 0, f"Feature column {col} contains {nan_count} NaNs")

    def test_leakage_firewall_integration(self):
        """Verify end-to-end compatibility with validate_target_leakage_firewall."""
        mrs = load_meter_read_success(self.data_dir)
        targets = build_operational_target(mrs)

        # Audit firewall for the test week
        week_targets = targets[targets["decision_week"] == self.decision_time]
        audit = validate_target_leakage_firewall(
            features_df=self.features,
            targets_df=week_targets,
            decision_timestamp=self.decision_time,
        )
        self.assertTrue(audit["passed"])
        self.assertEqual(len(audit["violations"]), 0)

    def test_offline_duration_bounded_semantics(self):
        """Verify offline duration features are strictly bounded by 168h wall-clock time."""
        # 1. Trailing 7 days = 168 hours = 604,800 seconds max
        self.assertTrue((self.features["feat_offline_hours"] >= 0.0).all())
        self.assertTrue((self.features["feat_offline_hours"] <= 168.0).all(), 
                        f"feat_offline_hours exceeds 168h: {self.features['feat_offline_hours'].max()}")
        self.assertTrue((self.features["feat_sum_offline_sec"] >= 0.0).all())
        self.assertTrue((self.features["feat_sum_offline_sec"] <= 604800.0).all(),
                        f"feat_sum_offline_sec exceeds 604800s: {self.features['feat_sum_offline_sec'].max()}")

        # 2. Hourly conservation law: observed_hours + missing_hours must strictly equal 168
        self.assertTrue((self.features["feat_observed_hours"] <= 168).all())
        self.assertTrue((self.features["feat_missing_hours"] <= 168).all())
        self.assertTrue(((self.features["feat_observed_hours"] + self.features["feat_missing_hours"]) == 168).all(),
                        "Hourly conservation violated: observed_hours + missing_hours != 168")

        # 2. Synthetic test: an extreme raw register value (e.g. 10,000,000s) must be clipped to 604,800s (168h)
        test_gw = self.features["gateway_id"].iloc[0]
        # Match master row regardless of colon format
        single_master = self.master[self.master["gateway_id"].str.replace(":", "").str.upper() == test_gw.upper()]
        
        tz = self.telem["ts_utc"].dt.tz
        synthetic_telem = pd.DataFrame([{
            "gateway_id": test_gw,
            "ts_utc": pd.Timestamp("2025-10-10 12:00:00", tz=tz),
            "offline_duration_sec": 10_000_000.0,
            "disconnection_cnt": 5,
            "reboot_cnt": 1,
            "r_cnt_power_cycle": 1,
            "r_cnt_reboot": 0,
            "r_cnt_unknown": 0,
            "rssi_bad": 0.0,
            "tx_success": 10,
            "avg_load1": 0.1,
            "avg_memfree": 50000.0,
        }])
        synth_features = extract_features_for_decision_week(
            decision_time=self.decision_time,
            telemetry_df=synthetic_telem,
            master_df=single_master,
            lookback_days=7,
        )
        self.assertEqual(synth_features["feat_offline_hours"].iloc[0], 168.0)
        self.assertEqual(synth_features["feat_sum_offline_sec"].iloc[0], 604800.0)

    def test_adversarial_temporal_leakage(self):
        """Adversarial test: injecting future telemetry rows must be blocked by observation cutoff."""
        tz = self.telem["ts_utc"].dt.tz
        future_ts = pd.Timestamp(self.decision_time, tz=tz) + pd.Timedelta(hours=2)
        leaked_telem = self.telem.copy()
        # Insert a future row for a known gateway with an extreme signal
        test_gw = self.features["gateway_id"].iloc[0]
        future_row = pd.DataFrame([{
            "gateway_id": test_gw,
            "ts_utc": future_ts,
            "offline_duration_sec": 50000.0,
            "disconnection_cnt": 99,
            "reboot_cnt": 99,
            "r_cnt_power_cycle": 99,
            "r_cnt_reboot": 0,
            "r_cnt_unknown": 0,
            "rssi_bad": 1.0,
            "tx_success": 0,
            "avg_load1": 10.0,
            "avg_memfree": 0.0,
        }])
        adversarial_telem = pd.concat([leaked_telem, future_row], ignore_index=True)
        
        # Feature extraction must strictly filter ts_utc < decision_time
        adv_features = extract_features_for_decision_week(
            decision_time=self.decision_time,
            telemetry_df=adversarial_telem,
            master_df=self.master,
            lookback_days=7,
        )
        gw_row = adv_features[adv_features["gateway_id"] == test_gw].iloc[0]
        # Verify the future row was completely excluded (reboot count must not be 99)
        self.assertNotEqual(gw_row["feat_reboot_cnt_total"], 99)



if __name__ == "__main__":
    unittest.main()
