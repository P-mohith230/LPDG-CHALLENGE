"""Unit tests for Innovation 4: Risk x Deterioration Priority Engine."""

import unittest
import pandas as pd
import numpy as np

from src.intelligence.priority_engine import compute_dispatch_priority


class TestInnovationPriority(unittest.TestCase):
    """Test suite for Risk x Deterioration Priority Engine."""

    def test_priority_formulations_and_quadrants(self):
        """Verify priority scores and quadrant classification."""
        df = pd.DataFrame([
            {"gateway_id": "000000000001", "risk_score": 0.90, "feat_deterioration_score": 0.80}, # Critical_Accelerating
            {"gateway_id": "000000000002", "risk_score": 0.85, "feat_deterioration_score": 0.20}, # Chronic_Persistent
            {"gateway_id": "000000000003", "risk_score": 0.40, "feat_deterioration_score": 0.85}, # Early_Warning_Emerging
            {"gateway_id": "000000000004", "risk_score": 0.10, "feat_deterioration_score": 0.10}, # Stable_Healthy
        ])

        # 1. Multiplicative
        res_mult = compute_dispatch_priority(df, method="multiplicative", beta=0.5)
        self.assertEqual(len(res_mult), 4)
        self.assertEqual(res_mult.iloc[0]["gateway_id"], "000000000001")
        self.assertEqual(res_mult[res_mult["gateway_id"] == "000000000003"]["quadrant_class"].iloc[0], "Early_Warning_Emerging")

        # 2. Additive
        res_add = compute_dispatch_priority(df, method="additive", alpha=0.7)
        self.assertTrue((res_add["priority_score"] >= 0.0).all())
        self.assertTrue((res_add["priority_score"] <= 1.0).all())

        # 3. Deterministic Sorting: Primary -priority, Secondary +gateway_id
        df_ties = pd.DataFrame([
            {"gateway_id": "00000000000b", "risk_score": 0.80, "feat_deterioration_score": 0.50},
            {"gateway_id": "00000000000a", "risk_score": 0.80, "feat_deterioration_score": 0.50},
        ])
        res_ties = compute_dispatch_priority(df_ties, method="multiplicative")
        self.assertEqual(res_ties.iloc[0]["gateway_id"], "00000000000A")
        self.assertEqual(res_ties.iloc[1]["gateway_id"], "00000000000B")


if __name__ == "__main__":
    unittest.main()
