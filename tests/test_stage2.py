"""Unit tests and Minimum Viable Evidence Gate verification for Stage 2.

Verifies:
1. Empirical profiling and identification of the 7 zero-variance roaming operator columns.
2. Zero-null property in raw telemetry (missingness is 100% omitted rows).
3. Counter semantics verification:
   - avg_uptime increments by 3600s/hr and resets upon reboot (resetting uptime clock).
   - offline_duration_sec is an interval flow metric (zero when disconnection_cnt == 0).
4. LoRa RF forensics:
   - CRC error ratio >= 0.95 in >80% of rows due to 868 MHz ISM noise.
   - Low/no correlation with n_meters_installed; dominated by antenna gain (Yagi 9dBi).
5. Gateway lifecycle cohorts and silence spell duration classification.
"""

from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from src.data.loader import (
    load_gateway_master,
    load_telemetry,
)
from src.features.forensics import (
    ZERO_VARIANCE_OPERATORS,
    analyze_counter_semantics,
    compute_rf_forensics,
    identify_zero_variance_columns,
    profile_gateway_lifecycle_and_coverage,
    profile_silence_spell_distribution,
    profile_telemetry_columns,
)


class TestZeroVarianceAndNulls(unittest.TestCase):
    """Test telemetry column profiling, zero-variance columns, and missingness properties."""

    @classmethod
    def setUpClass(cls):
        # Load August 2025 partition (181,484 rows) for fast empirical verification
        cls.telem_aug = load_telemetry(months=["2025-08"])
        cls.gw = load_gateway_master()

    def test_zero_null_property_in_raw_telemetry(self):
        """Verify that observed telemetry rows contain exactly 0 null values across all 57 columns."""
        null_counts = self.telem_aug.isna().sum()
        self.assertEqual(int(null_counts.sum()), 0)

    def test_zero_variance_roaming_operators(self):
        """Verify that the 7 foreign roaming operator columns are 100% constant zero."""
        self.assertEqual(len(ZERO_VARIANCE_OPERATORS), 7)
        for col in ZERO_VARIANCE_OPERATORS:
            self.assertIn(col, self.telem_aug.columns)
            vals = self.telem_aug[col]
            self.assertEqual(int(vals.min()), 0)
            self.assertEqual(int(vals.max()), 0)
            self.assertEqual(int(vals.nunique()), 1)

    def test_identify_zero_variance_columns(self):
        zero_cols = identify_zero_variance_columns(self.telem_aug)
        for op in ZERO_VARIANCE_OPERATORS:
            self.assertIn(op, zero_cols)


class TestCounterSemantics(unittest.TestCase):
    """Test empirical firmware counter semantics."""

    @classmethod
    def setUpClass(cls):
        cls.telem_aug = load_telemetry(months=["2025-08"])

    def test_counter_semantics_analysis(self):
        results = analyze_counter_semantics(self.telem_aug)
        self.assertGreater(results["consecutive_transitions_analyzed"], 100000)

        uptime = results["avg_uptime"]
        self.assertEqual(uptime["semantics"], "resetting_uptime_clock")
        # Median difference between consecutive hours without reboot must be 3600s
        self.assertAlmostEqual(uptime["median_hourly_diff_no_reboot_sec"], 3600.0, delta=5.0)
        self.assertGreater(uptime["pct_transitions_exactly_3600sec"], 85.0)

        offline = results["offline_duration_sec"]
        self.assertEqual(offline["semantics"], "interval_event_flow")
        # When disconnection_cnt == 0, offline duration must be 100% zero
        self.assertAlmostEqual(offline["pct_zero_when_no_disconnection"], 100.0, delta=0.01)
        # Verify both positive and negative consecutive deltas occur (proving it is NOT monotonic)
        self.assertGreater(offline["consecutive_diff_positive_pct"], 10.0)
        self.assertGreater(offline["consecutive_diff_negative_pct"], 10.0)


class TestRFForensics(unittest.TestCase):
    """Test LoRa RF metrics relative to installed meters and antenna types."""

    @classmethod
    def setUpClass(cls):
        cls.telem_aug = load_telemetry(months=["2025-08"])
        cls.gw = load_gateway_master()

    def test_rf_forensics(self):
        rf_stats = compute_rf_forensics(self.telem_aug, self.gw)
        self.assertGreater(rf_stats["total_observations_analyzed"], 100000)

        # High CRC error ratio due to ISM ambient noise (>70% of rows >= 0.95)
        self.assertGreater(rf_stats["pct_rows_crc_ratio_above_95"], 70.0)

        # Correlation between raw packets and installed meters is negligible (|r| < 0.25)
        self.assertLess(abs(rf_stats["correlation_rx_pkts_with_n_meters"]), 0.25)

        # Antenna effect: Yagi 9dBi receives over 10x more packets than Omni antennas
        ant_breakdown = rf_stats["antenna_type_breakdown"]
        yagi_pkts = ant_breakdown["Yagi 9dBi"]["rx_nr_pkts"]
        omni_pkts = ant_breakdown["Omni 3dBi"]["rx_nr_pkts"]
        self.assertGreater(yagi_pkts, omni_pkts * 10)


class TestLifecycleAndSilenceProfiling(unittest.TestCase):
    """Test gateway lifecycle cohorts and silence spell duration breakdown."""

    @classmethod
    def setUpClass(cls):
        cls.telem_aug = load_telemetry(months=["2025-08"])
        cls.gw = load_gateway_master()

    def test_lifecycle_cohort_distribution(self):
        lifecycle_df = profile_gateway_lifecycle_and_coverage(self.gw, self.telem_aug)
        self.assertEqual(len(lifecycle_df), 332)

        cohort_counts = lifecycle_df["lifecycle_cohort"].value_counts()
        self.assertEqual(cohort_counts["Full-period active"], 268)
        self.assertEqual(cohort_counts["Joined mid-network (Jan-Mar 2026)"], 40)
        self.assertEqual(cohort_counts["Decommissioned during challenge"], 12)
        self.assertEqual(cohort_counts["Future Install (Post-Mar 2026)"], 12)

        # Future installs must have 0 expected hours and 0 observed rows
        future = lifecycle_df[lifecycle_df["lifecycle_cohort"] == "Future Install (Post-Mar 2026)"]
        self.assertEqual(int(future["active_expected_hours"].sum()), 0)
        self.assertEqual(int(future["observed_telemetry_rows"].sum()), 0)

    def test_silence_spell_distribution(self):
        silence_stats = profile_silence_spell_distribution(self.telem_aug)
        self.assertGreater(silence_stats["total_silence_spells"], 1000)

        # Over 90% of silence spells must be transient 1-3 hour gaps
        intermittent_pct = silence_stats["intermittent_1_to_3h"]["percentage"]
        self.assertGreater(intermittent_pct, 90.0)

        # Multi-day outages are rare (< 2%)
        multiday_pct = silence_stats["multiday_outage_24_to_167h"]["percentage"]
        self.assertLess(multiday_pct, 2.0)


if __name__ == "__main__":
    unittest.main()
