"""Unit tests for Innovation 1: Deterioration Score Engine."""

import unittest
import pandas as pd
import numpy as np

from src.utils.config import get_data_dir
from src.data.loader import load_gateway_master, load_telemetry
from src.features.deterioration import (
    extract_deterioration_features_for_week,
    get_deterioration_feature_columns,
)


class TestInnovationDeterioration(unittest.TestCase):
    """Test suite for failure progression and deterioration features."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = get_data_dir()
        cls.master = load_gateway_master(cls.data_dir)
        cls.telem = load_telemetry(
            months=["2025-09", "2025-10"],
            columns=[
                "gateway_id",
                "ts_utc",
                "offline_duration_sec",
                "disconnection_cnt",
                "reboot_cnt",
                "r_cnt_power_cycle",
                "rssi_bad",
                "avg_load1",
            ],
            normalize_id="bare",
        )
        cls.decision_time = pd.Timestamp("2025-10-13 00:00:00")
        cls.det_df = extract_deterioration_features_for_week(
            decision_time=cls.decision_time,
            telemetry_df=cls.telem,
            lookback_days=28,
        )

    def test_feature_columns_and_nans(self):
        """Verify all deterioration feature columns exist and contain zero NaNs."""
        expected_cols = get_deterioration_feature_columns()
        for col in expected_cols:
            self.assertIn(col, self.det_df.columns)
            self.assertEqual(self.det_df[col].isna().sum(), 0, f"NaNs found in {col}")

    def test_deterioration_score_bounded_range(self):
        """Verify deterioration score is strictly bounded in [0.0, 1.0]."""
        scores = self.det_df["feat_deterioration_score"]
        self.assertTrue((scores >= 0.0).all())
        self.assertTrue((scores <= 1.0).all())
        self.assertGreater(scores.max(), 0.1)

    def test_cold_start_handling(self):
        """Verify handling of completely unseen/empty gateway history."""
        synth_telem = pd.DataFrame([{
            "gateway_id": "999999999999",
            "ts_utc": pd.Timestamp("2025-10-10 12:00:00"),
            "offline_duration_sec": 3600.0,
            "disconnection_cnt": 1,
            "reboot_cnt": 0,
            "r_cnt_power_cycle": 0,
            "rssi_bad": 0.0,
            "avg_load1": 0.5,
        }])
        res = extract_deterioration_features_for_week(
            decision_time=self.decision_time,
            telemetry_df=synth_telem,
            eligible_gateways=["999999999999", "888888888888"],
        )
        self.assertEqual(len(res), 2)
        # Empty gateway 888888888888 should have 0 NaNs
        row_empty = res[res["gateway_id"] == "888888888888"].iloc[0]
        self.assertEqual(row_empty["feat_det_has_history"], 0.0)
        self.assertFalse(np.isnan(row_empty["feat_deterioration_score"]))


if __name__ == "__main__":
    unittest.main()
