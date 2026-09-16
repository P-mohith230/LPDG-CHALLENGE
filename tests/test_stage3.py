"""Unit tests and Minimum Viable Evidence Gate verification for Stage 3.

Verifies:
1. E-01: Telemetry silence profiling, baseline 1-3h prevalence, and negative correlation with meter reads.
2. E-03: Offline duration transfer function, zero-dominance (>70% zero), and non-linear degradation.
3. E-04: Reboot cause attribution against field visits, distinguishing repaired vs no-fault visits while recognizing label noise.
4. E-05: Radio quality and CRC noise, proving CRC error saturation (r > 0.99 with packets) and cellular RSSI signal.
5. Cross-Analysis: Complementary relationship between offline duration and missing telemetry hours.
"""

from __future__ import annotations

import unittest
from src.experiments.stage3 import (
    run_experiment_e01,
    run_experiment_e03,
    run_experiment_e04,
    run_experiment_e05,
    run_stage3_cross_analysis,
)

# Use August and September 2025 partitions for fast unit test execution
TEST_MONTHS = ["2025-08", "2025-09"]


class TestStage3Experiments(unittest.TestCase):
    """Test Stage 3 research experiments and empirical assertions."""

    def test_e01_telemetry_silence(self):
        """Verify Experiment E-01 telemetry silence metrics and associations."""
        res = run_experiment_e01(months=TEST_MONTHS)
        self.assertEqual(res["experiment_id"], "E-01")
        self.assertGreater(res["total_gateway_weeks"], 1000)
        self.assertGreater(res["evaluable_predictive_weeks"], 800)

        # Baseline 1-3h silence must be the predominant operating mode (>50% of weeks)
        self.assertGreater(res["baseline_1_3h_pct"], 50.0)

        # Longer streaks must correlate negatively with meter read success
        self.assertLess(res["correlation_streak_read_ratio"], -0.10)
        self.assertGreater(res["correlation_streak_severe_deficit"], 0.10)

        # Contemporaneous and predictive tables must be populated
        self.assertIn("1-3h", res["contemporaneous_table"].index)
        self.assertIn("4-11h", res["contemporaneous_table"].index)
        self.assertIn("1-3h", res["predictive_streak_table"].index)
        self.assertIn("0h (perfect)", res["predictive_tail_table"].index)

    def test_e03_offline_duration_transfer_function(self):
        """Verify Experiment E-03 offline duration properties and transfer function."""
        res = run_experiment_e03(months=TEST_MONTHS)
        self.assertEqual(res["experiment_id"], "E-03")
        self.assertGreater(res["total_telemetry_rows"], 300000)

        # offline_duration_sec must be predominantly zero (>70%)
        self.assertGreater(res["zero_offline_rows_pct"], 70.0)

        # disconnections and offline duration must be positively correlated
        self.assertGreater(res["row_level_disc_offline_corr"], 0.40)
        self.assertGreater(res["weekly_disc_offline_corr"], 0.50)

        # Offline duration must correlate negatively with read ratio
        self.assertLess(res["corr_offline_read_ratio"], -0.10)
        self.assertGreater(res["corr_offline_severe_deficit"], 0.10)

        # Check bins in tables
        self.assertIn("1-6h", res["contemporaneous_table"].index)
        self.assertIn(">168h", res["contemporaneous_table"].index)

    def test_e04_reboot_cause_attribution(self):
        """Verify Experiment E-04 reboot attribution and field visit comparisons."""
        res = run_experiment_e04(months=TEST_MONTHS)
        self.assertEqual(res["experiment_id"], "E-04")
        self.assertGreater(res["evaluable_visits"], 50)

        # Fehler behoben visits must show higher mean reboots than Kein Fehler gefunden
        self.assertGreater(res["mean_reboot_repaired"], res["mean_reboot_nofault"])
        self.assertGreater(res["reboot_ratio_repaired_to_nofault"], 1.5)

        # Tables must contain expected categories
        self.assertIn("Fehler behoben", res["by_outcome_table"].index)
        self.assertIn("Kein Fehler gefunden", res["by_outcome_table"].index)

    def test_e05_radio_quality_and_crc_noise(self):
        """Verify Experiment E-05 radio quality, CRC saturation, and RSSI metrics."""
        res = run_experiment_e05(months=TEST_MONTHS)
        self.assertEqual(res["experiment_id"], "E-05")
        self.assertGreater(res["total_evaluable_weeks"], 1000)

        # CRC bad packets must correlate almost perfectly with total received packets
        self.assertGreater(res["corr_rx_pkts_crc_bad"], 0.99)

        # CRC ratio should NOT correlate strongly with meter read deficits (|r| < 0.15)
        self.assertLess(abs(res["corr_crc_ratio_severe_deficit"]), 0.15)

        # Poor RSSI must positively correlate with severe read deficit (> 0.10)
        self.assertGreater(res["corr_rssi_bad_severe_deficit"], 0.10)

        # Antenna table must contain known antenna types
        self.assertIn("Omni 3dBi", res["by_antenna_table"].index)
        self.assertIn("Yagi 9dBi", res["by_antenna_table"].index)

    def test_cross_analysis(self):
        """Verify Stage 3 cross-analysis relationships."""
        res = run_stage3_cross_analysis(months=TEST_MONTHS)

        # Offline duration and missing hours are complementary and positively correlated
        self.assertGreater(res["corr_offline_missing_hours"], 0.40)
        self.assertGreater(res["corr_disconnections_missing_hours"], 0.40)
        self.assertGreater(res["corr_reboots_disconnections"], 0.30)
        self.assertEqual(res["decommissioned_gateways_count"], 12)


if __name__ == "__main__":
    unittest.main()
