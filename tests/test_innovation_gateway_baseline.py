"""Unit tests for Innovation 3: Gateway-Specific Historical Baseline."""

import unittest
import pandas as pd
import numpy as np

from src.features.gateway_baseline import (
    extract_gateway_baselines_for_week,
    get_gateway_baseline_feature_columns,
)


class TestInnovationGatewayBaseline(unittest.TestCase):
    """Test suite for gateway-specific historical baseline engine."""

    def test_gateway_baseline_calculation_and_cold_start(self):
        """Verify gateway baseline computes Z-scores and falls back safely on cold-start."""
        # Create synthetic telemetry with 2 gateways:
        # Gateway 1 has 200 hours of history in days 8-28.
        # Gateway 2 has 0 hours of history (cold start).
        decision_time = pd.Timestamp("2025-10-20 00:00:00")
        recent_ts = pd.date_range("2025-10-13 00:00:00", "2025-10-19 23:00:00", freq="h")
        hist_ts = pd.date_range("2025-09-22 00:00:00", "2025-10-12 23:00:00", freq="h")

        rows = []
        # Gateway 1 history: steady state (offline=0, disconn=1, reboot=0)
        for t in hist_ts[:200]:
            rows.append({
                "gateway_id": "000000000001",
                "ts_utc": t,
                "offline_duration_sec": 0.0,
                "disconnection_cnt": 1,
                "reboot_cnt": 0,
                "r_cnt_power_cycle": 0,
            })
        # Gateway 1 recent: massive spike (offline=48h, disconn=15, reboot=10)
        for t in recent_ts[:100]:
            rows.append({
                "gateway_id": "000000000001",
                "ts_utc": t,
                "offline_duration_sec": 172800.0,  # 48h
                "disconnection_cnt": 15,
                "reboot_cnt": 10,
                "r_cnt_power_cycle": 2,
            })
        # Gateway 2: only recent rows (cold start)
        for t in recent_ts[:50]:
            rows.append({
                "gateway_id": "000000000002",
                "ts_utc": t,
                "offline_duration_sec": 3600.0,
                "disconnection_cnt": 2,
                "reboot_cnt": 1,
                "r_cnt_power_cycle": 0,
            })

        telem_df = pd.DataFrame(rows)
        res = extract_gateway_baselines_for_week(
            decision_time=decision_time,
            telemetry_df=telem_df,
            history_days=28,
            min_history_hours=72,
        )

        self.assertEqual(len(res), 2)
        cols = get_gateway_baseline_feature_columns()
        for c in cols:
            self.assertIn(c, res.columns)
            self.assertEqual(res[c].isna().sum(), 0)

        # Gateway 1: Adequate history
        gw1 = res[res["gateway_id"] == "000000000001"].iloc[0]
        self.assertEqual(gw1["feat_gw_has_adequate_history"], 1.0)
        self.assertGreater(gw1["feat_gw_z_offline"], 0.0)
        self.assertGreater(gw1["feat_gw_relative_anomaly_score"], 0.5)

        # Gateway 2: Cold start fallback
        gw2 = res[res["gateway_id"] == "000000000002"].iloc[0]
        self.assertEqual(gw2["feat_gw_has_adequate_history"], 0.0)
        self.assertEqual(gw2["feat_gw_hist_obs_hours"], 0)
        self.assertTrue(0.0 <= gw2["feat_gw_relative_anomaly_score"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
