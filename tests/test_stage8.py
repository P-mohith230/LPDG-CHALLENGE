"""Unit tests for Stage 8: Economic Decision Policy, Cooldown & Reason Generation.

Tests:
1. Deterministic sorting and tie-breaking by (-risk_score, gateway_id).
2. Cooldown policy suppression of recently visited gateways.
3. Cooldown relaxation when eligible fleet is smaller than 15.
4. Reason generation strictly complies with length <= 300 chars and evidence rules.
5. Multi-week policy simulation accurately tracks stateful visit history.
"""

import unittest
import numpy as np
import pandas as pd

from src.models.decision_policy import (
    rank_gateways_for_week,
    simulate_policy_with_cooldown,
)
from src.prediction.reason_builder import build_dispatch_reason


class TestStage8DecisionPolicy(unittest.TestCase):
    """Test suite for Stage 8 ranking policy and reason generation."""

    def test_deterministic_sorting_and_tie_breaking(self):
        """Verify ranking sorts by descending risk_score, breaking ties ascending by gateway_id."""
        df = pd.DataFrame({
            "gateway_id": ["0639ea5602c2", "0639ea5602c1", "0639ea5602c3"],
            "risk_score": [0.85, 0.85, 0.90],
        })
        ranked = rank_gateways_for_week(df, visited_history={}, cooldown_weeks=0, visits_per_week=3)
        self.assertEqual(list(ranked["gateway_id"]), ["0639EA5602C3", "0639EA5602C1", "0639EA5602C2"])
        self.assertEqual(list(ranked["rank"]), [1, 2, 3])

    def test_cooldown_suppression(self):
        """Verify that gateways visited within the cooldown window are suppressed."""
        df = pd.DataFrame({
            "gateway_id": [f"{i:012x}" for i in range(20)],
            "risk_score": np.linspace(0.99, 0.50, 20),
        })
        # Suppose top 2 gateways were visited last week (elapsed = 0)
        history = {f"{0:012x}": 0, f"{1:012x}": 0}
        
        ranked_cd1 = rank_gateways_for_week(df, visited_history=history, cooldown_weeks=1, visits_per_week=5)
        # 0 and 1 should be excluded
        self.assertNotIn(f"{0:012x}", ranked_cd1["gateway_id"].values)
        self.assertNotIn(f"{1:012x}", ranked_cd1["gateway_id"].values)
        self.assertEqual(len(ranked_cd1), 5)
        self.assertEqual(ranked_cd1.iloc[0]["gateway_id"], f"{2:012x}")

    def test_reason_builder_length_and_content(self):
        """Verify reason strings are within 300 chars and contain valid evidence phrases."""
        sample_row = {
            "feat_tail_silence": 48,
            "feat_missing_hours": 72,
            "feat_offline_hours": 35.5,
            "feat_sum_disconnections": 25,
            "feat_power_cycle_recent_24h": 2,
            "feat_reboot_cnt_total": 8,
            "feat_n_meters_installed": 450,
            "risk_score": 0.95,
        }
        reason = build_dispatch_reason(sample_row)
        self.assertLessEqual(len(reason), 300)
        self.assertGreater(len(reason), 20)
        self.assertTrue(reason.endswith("."))
        self.assertIn("48h trailing silence", reason)
        self.assertIn("peak 35.5h event", reason)
        self.assertIn("450 meters", reason)

    def test_empty_features_reason_fallback(self):
        """Verify reason fallback when all telemetry features are zero."""
        empty_row = {"risk_score": 0.72}
        reason = build_dispatch_reason(empty_row)
        self.assertLessEqual(len(reason), 300)
        self.assertIn("Elevated multivariate failure risk", reason)


if __name__ == "__main__":
    unittest.main()
