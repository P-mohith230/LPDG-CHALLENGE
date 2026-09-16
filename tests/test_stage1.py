"""Unit tests and Minimum Viable Evidence Gate verification for Stage 1.

Verifies:
1. Normalizer correctness, round-trip lossless property, and validation logic.
2. Exact raw row counts and column dimensions across all 5 challenge datasets.
3. ID representation conformity ([OBSERVED IN DATA]).
4. Dynamic partition discovery without hardcoded month paths.
5. Continuous UTC timestamp parsing without local DST distortion.
6. Time-grid alignment and omitted telemetry row (silence) detection.
"""

from __future__ import annotations

import unittest
import pandas as pd
from pathlib import Path

from src.utils.config import (
    DATA_DIR,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
    TOTAL_SUBMISSION_ROWS,
    VISIT_COST_EUR,
    FAULT_COST_WEEKLY_EUR,
    TOTAL_FIXED_VISIT_BUDGET_EUR,
    MAX_REASON_CHARS,
    get_data_dir,
)
from src.utils.normalizer import (
    is_valid_gateway_id,
    normalize_series,
    to_bare_hex,
    to_colon_hex,
)
from src.data.loader import (
    discover_telemetry_partitions,
    load_engineer_review,
    load_field_visits,
    load_gateway_master,
    load_meter_read_success,
    load_telemetry,
)
from src.data.time_grid import (
    align_telemetry_to_grid,
    build_hourly_grid,
    compute_silence_spells,
    find_missing_hours,
)


class TestConfigAndConstants(unittest.TestCase):
    """Test project configuration and official LPDG constants."""

    def test_official_economic_constants(self):
        self.assertEqual(len(SCORED_WEEKS), 8)
        self.assertEqual(VISITS_PER_WEEK, 15)
        self.assertEqual(TOTAL_SUBMISSION_ROWS, 120)
        self.assertEqual(VISIT_COST_EUR, 380.0)
        self.assertEqual(FAULT_COST_WEEKLY_EUR, 600.0)
        self.assertEqual(TOTAL_FIXED_VISIT_BUDGET_EUR, 45600.0)
        self.assertEqual(MAX_REASON_CHARS, 300)

    def test_data_dir_resolution(self):
        data_dir = get_data_dir()
        self.assertTrue(data_dir.is_dir())
        self.assertTrue((data_dir / "gateway_master.csv").is_file())


class TestNormalizer(unittest.TestCase):
    """Test bidirectional gateway ID normalizer and format validation."""

    def test_to_bare_hex(self):
        # 17-char colon hex to 12-char bare hex
        self.assertEqual(to_bare_hex("06:39:EA:56:02:C1"), "0639EA5602C1")
        # Lowercase colon hex
        self.assertEqual(to_bare_hex("06:39:ea:56:02:c1"), "0639EA5602C1")
        # Bare hex (identity uppercase)
        self.assertEqual(to_bare_hex("0639ea5602c1"), "0639EA5602C1")
        # Whitespace handling
        self.assertEqual(to_bare_hex("  06:39:EA:56:02:C1 \n"), "0639EA5602C1")

    def test_to_colon_hex(self):
        # 12-char bare hex to 17-char colon hex
        self.assertEqual(to_colon_hex("0639EA5602C1"), "06:39:EA:56:02:C1")
        # Lowercase bare hex
        self.assertEqual(to_colon_hex("0639ea5602c1"), "06:39:EA:56:02:C1")
        # Colon hex (identity uppercase)
        self.assertEqual(to_colon_hex("06:39:ea:56:02:c1"), "06:39:EA:56:02:C1")
        # Whitespace handling
        self.assertEqual(to_colon_hex("  0639ea5602c1 \t"), "06:39:EA:56:02:C1")

    def test_lossless_round_trip(self):
        sample_bare = "0202CB0A6B1F"
        sample_colon = "06:39:EA:56:02:C1"
        self.assertEqual(to_bare_hex(to_colon_hex(sample_bare)), sample_bare)
        self.assertEqual(to_colon_hex(to_bare_hex(sample_colon)), sample_colon)

    def test_invalid_gateway_id(self):
        invalid_cases = [
            "06:39:EA:56:02",       # Too short colon
            "06:39:EA:56:02:C1:99", # Too long colon
            "0639EA5602",          # Too short bare
            "0639EA5602C199",      # Too long bare
            "06:39:EA:56:02:ZZ",   # Non-hex characters
            "NOT_AN_ID",
            "",
        ]
        for val in invalid_cases:
            self.assertFalse(is_valid_gateway_id(val), f"Expected False for {val!r}")
            with self.assertRaises(ValueError):
                to_bare_hex(val)
            with self.assertRaises(ValueError):
                to_colon_hex(val)

    def test_normalize_series(self):
        s = pd.Series(["06:39:EA:56:02:C1", "0202cb0a6b1f"])
        bare_s = normalize_series(s, target_format="bare")
        self.assertEqual(list(bare_s), ["0639EA5602C1", "0202CB0A6B1F"])
        colon_s = normalize_series(bare_s, target_format="colon")
        self.assertEqual(list(colon_s), ["06:39:EA:56:02:C1", "02:02:CB:0A:6B:1F"])


class TestDataLoaderAndDimensions(unittest.TestCase):
    """Test loading data files and verify exact file dimensions ([OBSERVED IN DATA])."""

    def test_load_gateway_master_dimensions(self):
        df = load_gateway_master()
        self.assertEqual(df.shape, (332, 11))
        # Verify raw colon hex ID format
        self.assertTrue(df["gateway_id"].str.contains(":").all())
        # Verify normalization option
        df_bare = load_gateway_master(normalize_id="bare")
        self.assertFalse(df_bare["gateway_id"].str.contains(":").any())
        self.assertTrue((df_bare["gateway_id"].str.len() == 12).all())

    def test_load_field_visits_dimensions(self):
        df = load_field_visits()
        self.assertEqual(df.shape, (642, 8))
        # Verify raw colon hex ID format
        self.assertTrue(df["gateway_id"].str.contains(":").all())

    def test_load_meter_read_success_dimensions(self):
        df = load_meter_read_success()
        self.assertEqual(df.shape, (7226, 4))
        # Verify raw bare hex ID format
        self.assertFalse(df["gateway_id"].str.contains(":").any())
        self.assertTrue((df["gateway_id"].str.len() == 12).all())

    def test_load_engineer_review_dimensions(self):
        df = load_engineer_review()
        self.assertEqual(df.shape, (120, 6))
        # Verify raw colon hex ID format
        self.assertTrue(df["gateway_id"].str.contains(":").all())

    def test_dynamic_telemetry_partition_discovery(self):
        partitions = discover_telemetry_partitions()
        self.assertEqual(len(partitions), 8)
        partition_names = [p.name for p in partitions]
        expected_partitions = [
            "month=2025-08",
            "month=2025-09",
            "month=2025-10",
            "month=2025-11",
            "month=2025-12",
            "month=2026-01",
            "month=2026-02",
            "month=2026-03",
        ]
        self.assertEqual(partition_names, expected_partitions)

    def test_load_single_month_telemetry(self):
        # Test loading single month partition with dynamic discovery
        df_aug = load_telemetry(months=["2025-08"])
        self.assertEqual(len(df_aug), 181484)
        self.assertEqual(df_aug.shape[1], 57)
        # Verify ts_utc is continuous UTC datetime
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df_aug["ts_utc"]))
        self.assertEqual(str(df_aug["ts_utc"].dt.tz), "UTC")
        # Verify DateDt and hour reference columns exist
        self.assertIn("DateDt", df_aug.columns)
        self.assertIn("hour", df_aug.columns)

    def test_all_telemetry_partitions_total_rows(self):
        # Minimum Viable Evidence Gate: exact 1,433,387 telemetry rows
        partitions = discover_telemetry_partitions()
        import pyarrow.parquet as pq
        total_rows = sum(pq.read_table(p).num_rows for p in partitions)
        self.assertEqual(total_rows, 1433387)

    def test_normalized_id_cross_dataset_integrity(self):
        """Verify that all gateways across operational datasets exist in gateway_master."""
        gw = load_gateway_master(normalize_id="bare")
        gw_ids = set(gw["gateway_id"])

        mrs = load_meter_read_success(normalize_id="bare")
        mrs_ids = set(mrs["gateway_id"])
        self.assertTrue(mrs_ids.issubset(gw_ids))
        self.assertEqual(len(mrs_ids), 299)

        fv = load_field_visits(normalize_id="bare")
        fv_ids = set(fv["gateway_id"])
        self.assertTrue(fv_ids.issubset(gw_ids))
        self.assertEqual(len(fv_ids), 247)

        er = load_engineer_review(normalize_id="bare")
        er_ids = set(er["gateway_id"])
        self.assertTrue(er_ids.issubset(gw_ids))
        self.assertEqual(len(er_ids), 120)


class TestTimeGridAndSilenceDetection(unittest.TestCase):
    """Test time-grid creation, omitted row detection, and silence streak calculation."""

    def test_build_hourly_grid(self):
        gateways = ["GW0000000001", "GW0000000002"]
        start_utc = "2025-08-01T00:00:00Z"
        end_utc = "2025-08-01T23:00:00Z"  # 24 hours
        grid = build_hourly_grid(gateways, start_utc, end_utc)
        self.assertEqual(len(grid), 2 * 24)
        self.assertEqual(list(grid.columns), ["gateway_id", "ts_utc"])

    def test_find_missing_hours(self):
        gateways = ["GW0000000001"]
        start_utc = "2025-08-01T00:00:00Z"
        end_utc = "2025-08-01T03:00:00Z"  # 4 hours: 00, 01, 02, 03

        # Simulate telemetry missing hour 02
        t_data = pd.DataFrame({
            "gateway_id": ["GW0000000001", "GW0000000001", "GW0000000001"],
            "ts_utc": [
                pd.Timestamp("2025-08-01T00:00:00Z"),
                pd.Timestamp("2025-08-01T01:00:00Z"),
                pd.Timestamp("2025-08-01T03:00:00Z"),
            ],
            "rx_nr_pkts": [10, 15, 20],
        })

        missing = find_missing_hours(t_data, gateways, start_utc, end_utc)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing.iloc[0]["gateway_id"], "GW0000000001")
        self.assertEqual(missing.iloc[0]["ts_utc"], pd.Timestamp("2025-08-01T02:00:00Z"))

    def test_align_telemetry_to_grid(self):
        gateways = ["GW0000000001"]
        start_utc = "2025-08-01T00:00:00Z"
        end_utc = "2025-08-01T02:00:00Z"  # 3 hours: 00, 01, 02

        # Telemetry has only hour 00
        t_data = pd.DataFrame({
            "gateway_id": ["GW0000000001"],
            "ts_utc": [pd.Timestamp("2025-08-01T00:00:00Z")],
            "rx_nr_pkts": [42],
        })

        aligned = align_telemetry_to_grid(t_data, gateways, start_utc, end_utc)
        self.assertEqual(len(aligned), 3)
        self.assertEqual(list(aligned["is_omitted"]), [False, True, True])
        self.assertEqual(aligned.iloc[0]["rx_nr_pkts"], 42)
        self.assertTrue(pd.isna(aligned.iloc[1]["rx_nr_pkts"]))

    def test_compute_silence_spells(self):
        gateways = ["GW0000000001"]
        start_utc = "2025-08-01T00:00:00Z"
        end_utc = "2025-08-01T04:00:00Z"  # 5 hours: 00, 01, 02, 03, 04

        # Telemetry has hours 00 and 02. Hours 01, 03, 04 are missing.
        t_data = pd.DataFrame({
            "gateway_id": ["GW0000000001", "GW0000000001"],
            "ts_utc": [
                pd.Timestamp("2025-08-01T00:00:00Z"),
                pd.Timestamp("2025-08-01T02:00:00Z"),
            ],
        })

        stats = compute_silence_spells(t_data, gateways, start_utc, end_utc)
        self.assertEqual(len(stats), 1)
        row = stats.iloc[0]
        self.assertEqual(row["total_expected_hours"], 5)
        self.assertEqual(row["observed_hours"], 2)
        self.assertEqual(row["missing_hours"], 3)
        self.assertEqual(row["missing_pct"], 60.0)
        self.assertEqual(row["max_consecutive_silence_hours"], 2)  # hours 03, 04
        self.assertEqual(row["current_silence_streak_hours"], 2)   # ends on streak of 2


if __name__ == "__main__":
    unittest.main()
