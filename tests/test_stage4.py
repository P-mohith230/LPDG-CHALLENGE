"""Unit tests for Stage 4: Operational Target Definition & Label-Quality Investigation.

Tests:
1. Operational target generation from meter_read_success.csv.
2. Binary target validity: values strictly in {0, 1}, no NaNs in valid pairs.
3. Target prevalence and stability across historical period.
4. Rejection of binary zero-reads target (N=2, prevalence < 0.1%).
5. Candidate target generation (A, B, C, D).
6. Leakage firewall validator: passes clean inputs and catches timestamp / column violations.
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.config import get_data_dir
from src.data.loader import load_meter_read_success, load_field_visits
from src.models.target import (
    DEFAULT_DEFICIT_THRESHOLD,
    DEFAULT_TARGET_NAME,
    build_operational_target,
    build_candidate_targets,
    validate_target_leakage_firewall,
)


class TestStage4TargetDefinition(unittest.TestCase):
    """Test suite for operational target construction and validation."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = get_data_dir()
        cls.mrs = load_meter_read_success(cls.data_dir)
        cls.target_df = build_operational_target(cls.mrs)

    def test_target_dimensions_and_columns(self):
        """Verify output schema of build_operational_target."""
        expected_cols = [
            "gateway_id",
            "decision_week",
            "target_week",
            "target_meters_read",
            "target_meters_expected",
            "target_read_ratio",
            DEFAULT_TARGET_NAME,
        ]
        for col in expected_cols:
            self.assertIn(col, self.target_df.columns)

        # Ensure no nulls in target column
        self.assertEqual(self.target_df[DEFAULT_TARGET_NAME].isna().sum(), 0)

        # Ensure values are strictly binary integers {0, 1}
        unique_vals = set(self.target_df[DEFAULT_TARGET_NAME].unique())
        self.assertTrue(unique_vals.issubset({0, 1}))

    def test_temporal_lead_alignment(self):
        """Verify target_week is strictly exactly 7 days after decision_week - 7 days (i.e. target_week == decision_week)."""
        # For horizon_weeks = 1:
        # Features observe week k [week_start, week_start + 7d)
        # Decision week = week_start + 7d
        # Target week = week_start + 7d (evaluating week k+1)
        time_diff = self.target_df["target_week"] - self.target_df["decision_week"]
        self.assertTrue((time_diff == pd.Timedelta(days=0)).all())

    def test_target_prevalence_and_gateways(self):
        """Verify empirical prevalence of settled target (read_ratio < 0.50)."""
        total = len(self.target_df)
        positives = int(self.target_df[DEFAULT_TARGET_NAME].sum())
        prevalence = positives / total

        # In actual dataset, N=6,927, pos=551, prev ~7.95%
        self.assertGreaterEqual(total, 6900)
        self.assertGreaterEqual(positives, 500)
        self.assertLessEqual(positives, 650)
        self.assertAlmostEqual(prevalence, 0.0795, delta=0.015)

        # Unique gateways with at least one deficit
        n_faulty_gw = self.target_df[self.target_df[DEFAULT_TARGET_NAME] == 1]["gateway_id"].nunique()
        self.assertGreaterEqual(n_faulty_gw, 90)
        self.assertLessEqual(n_faulty_gw, 120)

    def test_rejection_of_zero_read_target(self):
        """Verify that binary zero reads (meters_read == 0) is statistically degenerated (< 0.1% prevalence)."""
        zero_reads = (self.target_df["target_meters_read"] == 0).sum()
        zero_read_prev = zero_reads / len(self.target_df)
        self.assertEqual(zero_reads, 2)
        self.assertLess(zero_read_prev, 0.001)

    def test_candidate_targets_builder(self):
        """Verify build_candidate_targets outputs all alternative candidate targets."""
        candidates = build_candidate_targets(self.mrs)
        expected_candidates = [
            "target_severe_deficit_50",
            "target_severe_deficit_30",
            "target_severe_deficit_80",
            "target_zero_read",
            "target_persistent_deficit",
        ]
        for c in expected_candidates:
            self.assertIn(c, candidates.columns)

        # Verify hierarchical ordering of deficit thresholds
        # deficit_80 >= deficit_50 >= deficit_30 >= zero_read
        sum_80 = candidates["target_severe_deficit_80"].sum()
        sum_50 = candidates["target_severe_deficit_50"].sum()
        sum_30 = candidates["target_severe_deficit_30"].sum()
        sum_0 = candidates["target_zero_read"].sum()
        self.assertGreater(sum_80, sum_50)
        self.assertGreater(sum_50, sum_30)
        self.assertGreater(sum_30, sum_0)

    def test_leakage_firewall_validation(self):
        """Verify that validate_target_leakage_firewall accepts valid data and raises on leakage."""
        decision_time = pd.Timestamp("2025-10-06 00:00:00")

        # 1. Clean synthetic features (timestamp strictly before decision_time)
        clean_features = pd.DataFrame({
            "gateway_id": ["0639EA5602C1", "0639EA5602C2"],
            "decision_week": [decision_time, decision_time],
            "observation_cutoff_utc": [pd.Timestamp("2025-10-05 23:59:59"), pd.Timestamp("2025-10-05 23:00:00")],
            "feature_silence_hours": [3, 12],
        })
        clean_targets = pd.DataFrame({
            "gateway_id": ["0639EA5602C1", "0639EA5602C2"],
            "target_week": [decision_time, decision_time],
            "target_severe_deficit": [0, 1],
        })

        # Should pass cleanly
        audit = validate_target_leakage_firewall(clean_features, clean_targets, decision_time)
        self.assertTrue(audit["passed"])

        # 2. Leaky features (feature timestamp after decision boundary)
        leaky_features = clean_features.copy()
        leaky_features.loc[0, "observation_cutoff_utc"] = pd.Timestamp("2025-10-06 01:00:00")
        with self.assertRaises(ValueError):
            validate_target_leakage_firewall(leaky_features, clean_targets, decision_time)

        # 3. Leaky column name (target column included in feature matrix)
        column_leaky_features = clean_features.copy()
        column_leaky_features["target_severe_deficit"] = [0, 1]
        with self.assertRaises(ValueError):
            validate_target_leakage_firewall(column_leaky_features, clean_targets, decision_time)


if __name__ == "__main__":
    unittest.main()
