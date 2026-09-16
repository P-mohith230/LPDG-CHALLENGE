"""Unit tests for dashboard services and data integrity.

Verifies:
- PredictionService schema, integrity, and KPI derivations.
- FeatureService 32 C3 feature count and 5 failure signatures.
- GatewayService 3D node coordinate projection and elevation encoding.
- EconomicService official challenge parameters and historical benchmark data.
- ModelService C0–C10 trade-off data extraction.
"""

from __future__ import annotations

import unittest
from app.services.economic_service import EconomicService
from app.services.feature_service import FeatureService
from app.services.gateway_service import GatewayService
from app.services.model_service import ModelService
from app.services.prediction_service import EXPECTED_SHA256, PredictionService


class TestDashboardServices(unittest.TestCase):
    """Test suite for application service layer."""

    def setUp(self) -> None:
        self.pred_service = PredictionService()
        self.gw_service = GatewayService(prediction_service=self.pred_service)

    def test_predictions_service_integrity_and_shape(self) -> None:
        """Verify predictions.csv SHA256 matches expected checksum and contains 120 rows."""
        is_valid, digest = self.pred_service.verify_integrity()
        self.assertTrue(is_valid, f"SHA256 mismatch: {digest} != {EXPECTED_SHA256}")

        df = self.pred_service.get_all_predictions()
        self.assertEqual(len(df), 120, "Must contain exactly 120 rows")

        weeks = self.pred_service.get_scored_weeks()
        self.assertEqual(len(weeks), 8, "Must cover exactly 8 competition weeks")

        for w in weeks:
            week_df = self.pred_service.get_predictions_for_week(w)
            self.assertEqual(len(week_df), 15, f"Week {w} must have exactly 15 rows")
            self.assertEqual(list(week_df["rank"]), list(range(1, 16)), "Ranks must be 1 to 15")

    def test_kpi_calculations(self) -> None:
        """Verify KPI calculations for the first week."""
        weeks = self.pred_service.get_scored_weeks()
        kpis = self.pred_service.get_kpis_for_week(weeks[0])
        self.assertEqual(kpis["available_visits"], 15)
        self.assertGreater(kpis["avg_risk"], 0.5)
        self.assertGreaterEqual(kpis["above_threshold_count"], 1)
        self.assertEqual(kpis["weekly_visit_budget"], 5700.0)

    def test_feature_service_registry(self) -> None:
        """Verify C3 feature breakdown: exactly 29 baseline + 3 gateway self-baselines = 32 total."""
        counts = FeatureService.get_feature_counts()
        self.assertEqual(counts["total_c3_features"], 32)
        self.assertEqual(counts["gateway_self_baselines"], 3)

        all_features = FeatureService.get_all_c3_features()
        self.assertEqual(len(all_features), 32)
        self.assertIn("feat_gw_z_offline", all_features)
        self.assertIn("feat_gw_z_missing", all_features)
        self.assertIn("feat_gw_relative_anomaly_score", all_features)

        signatures = FeatureService.get_failure_signatures()
        self.assertEqual(len(signatures), 5, "Must contain exactly 5 failure signatures in registry")

    def test_gateway_service_node_elevation_encoding(self) -> None:
        """Verify 3D node representation encodes elevation directly from risk."""
        weeks = self.pred_service.get_scored_weeks()
        demo_nodes = self.gw_service.get_fleet_nodes_for_week(weeks[0], demo_mode=True)
        self.assertGreater(len(demo_nodes), 0)

        for n in demo_nodes:
            self.assertIn("elevation", n)
            self.assertIn("risk", n)
            self.assertIn("color", n)
            # In demo mode, all synthetic nodes have synthetic risk and elevation
            self.assertAlmostEqual(n["elevation"], n["risk"] * 14.0, places=1)

        # In real data mode: verify dispatched nodes have elevation while undispatched rest on ground datum
        real_nodes = self.gw_service.get_fleet_nodes_for_week(weeks[0], demo_mode=False)
        dispatched_count = sum(1 for n in real_nodes if n["is_dispatched"])
        self.assertEqual(dispatched_count, 15, "Exactly 15 gateways must be dispatched")

        for n in real_nodes:
            if n["is_dispatched"]:
                self.assertIsNotNone(n["risk"])
                self.assertAlmostEqual(n["elevation"], n["risk"] * 14.0, places=1)
            else:
                self.assertIsNone(n["risk"])
                self.assertEqual(n["elevation"], 0.0)

    def test_economic_service_horizon_separation(self) -> None:
        """Verify EconomicService strictly separates 8-week challenge from 16-week benchmark."""
        off = EconomicService.get_official_challenge_parameters()
        self.assertEqual(off["scored_weeks_count"], 8)
        self.assertEqual(off["total_visits"], 120)
        self.assertEqual(off["fixed_visit_budget_eur"], 45600.0)

        hist = EconomicService.get_historical_benchmark_data()
        self.assertEqual(hist["c3_production"]["total_cost_eur"], 115200.0)
        self.assertEqual(hist["c0_baseline_v1"]["total_cost_eur"], 128400.0)
        self.assertEqual(hist["three_sigma"]["total_cost_eur"], 164400.0)
        self.assertAlmostEqual(hist["savings_vs_3sigma_pct"], -29.93, places=1)

    def test_what_if_simulation_isolation(self) -> None:
        """Verify What-If simulation outputs disclaimer and does not alter predictions."""
        sim = EconomicService.simulate_what_if_capacity(weekly_capacity=20)
        self.assertEqual(sim["weekly_capacity"], 20)
        self.assertEqual(sim["total_visits"], 160)
        self.assertIn("EXPLORATION ONLY", sim["disclaimer"])

        # Check that predictions.csv is still untouched
        is_valid, _ = self.pred_service.verify_integrity()
        self.assertTrue(is_valid)

    def test_model_service_configurations(self) -> None:
        """Verify ModelService loads all 11 configurations C0-C10."""
        df_cfg = ModelService.get_configuration_trade_offs()
        self.assertEqual(len(df_cfg), 11, "Must contain 11 evaluated configurations")
        c3_row = df_cfg[df_cfg["config_id"] == "C3"].iloc[0]
        self.assertEqual(c3_row["total_cost_eur"], 115200.0)
        self.assertEqual(c3_row["feature_count"], 32)
        self.assertEqual(c3_row["status"], "Selected Production Architecture")


if __name__ == "__main__":
    unittest.main()
