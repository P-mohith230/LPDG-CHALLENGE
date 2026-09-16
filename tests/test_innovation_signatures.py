"""Unit tests for Innovation 2: Failure Signature Engine."""

import unittest
import pandas as pd
import numpy as np

from src.intelligence.failure_signatures import (
    evaluate_failure_signatures,
    get_signature_feature_columns,
    SIGNATURE_REGISTRY,
)


class TestInnovationSignatures(unittest.TestCase):
    """Test suite for failure signature engine."""

    def test_signature_evaluation_on_synthetic_data(self):
        """Verify each signature triggers on appropriate threshold breaches."""
        test_df = pd.DataFrame([
            # Gateway 1: Clean, zero signals
            {
                "gateway_id": "000000000001",
                "feat_offline_hours": 0.0,
                "feat_sum_disconnections": 0,
                "feat_missing_hours": 0,
                "feat_tail_silence": 0,
                "feat_power_cycle_recent_24h": 0,
                "feat_power_cycle_cnt": 0,
                "feat_reboot_cnt_total": 0,
                "feat_mean_rssi_bad": 0.0,
                "feat_mean_load1": 0.5,
                "feat_tot_tx_success": 100,
            },
            # Gateway 2: Backhaul collapse (sig 1)
            {
                "gateway_id": "000000000002",
                "feat_offline_hours": 48.0,
                "feat_sum_disconnections": 10,
                "feat_missing_hours": 24,
                "feat_tail_silence": 0,
                "feat_power_cycle_recent_24h": 0,
                "feat_power_cycle_cnt": 0,
                "feat_reboot_cnt_total": 0,
                "feat_mean_rssi_bad": 0.0,
                "feat_mean_load1": 0.5,
                "feat_tot_tx_success": 100,
            },
            # Gateway 3: Hardware power cycle surge (sig 2)
            {
                "gateway_id": "000000000003",
                "feat_offline_hours": 0.0,
                "feat_sum_disconnections": 0,
                "feat_missing_hours": 0,
                "feat_tail_silence": 0,
                "feat_power_cycle_recent_24h": 2,
                "feat_power_cycle_cnt": 4,
                "feat_reboot_cnt_total": 8,
                "feat_mean_rssi_bad": 0.0,
                "feat_mean_load1": 0.5,
                "feat_tot_tx_success": 100,
            },
            # Gateway 4: Prolonged blackout (sig 3)
            {
                "gateway_id": "000000000004",
                "feat_offline_hours": 0.0,
                "feat_sum_disconnections": 0,
                "feat_missing_hours": 100,
                "feat_tail_silence": 48,
                "feat_power_cycle_recent_24h": 0,
                "feat_power_cycle_cnt": 0,
                "feat_reboot_cnt_total": 0,
                "feat_mean_rssi_bad": 0.0,
                "feat_mean_load1": 0.5,
                "feat_tot_tx_success": 100,
            },
        ])

        sigs = evaluate_failure_signatures(test_df)
        self.assertEqual(len(sigs), 4)

        # Gateway 1: No active signatures
        self.assertEqual(sigs.iloc[0]["sig_active_count"], 0)
        self.assertEqual(sigs.iloc[0]["feat_signature_score"], 0.0)
        self.assertEqual(sigs.iloc[0]["sig_diagnostic_tags"], "None")

        # Gateway 2: Sig 1 active
        self.assertEqual(sigs.iloc[1]["sig_01_connectivity_collapse"], 1)
        self.assertIn("Backhaul Outage Pattern", sigs.iloc[1]["sig_diagnostic_tags"])

        # Gateway 3: Sig 2 active
        self.assertEqual(sigs.iloc[2]["sig_02_hardware_power_cycle_surge"], 1)
        self.assertIn("Power-Cycle Instability", sigs.iloc[2]["sig_diagnostic_tags"])

        # Gateway 4: Sig 3 active
        self.assertEqual(sigs.iloc[3]["sig_03_persistent_silence_blackout"], 1)
        self.assertIn("Prolonged Telemetry Blackout", sigs.iloc[3]["sig_diagnostic_tags"])

    def test_signature_columns_list(self):
        """Verify get_signature_feature_columns returns valid registered columns."""
        cols = get_signature_feature_columns()
        self.assertIn("feat_signature_score", cols)
        self.assertIn("sig_active_count", cols)
        self.assertEqual(len(cols), 7)


if __name__ == "__main__":
    unittest.main()
