"""Unit tests for Innovation 5: Novelty & OOD Detector."""

import unittest
import pandas as pd
import numpy as np

from src.intelligence.novelty import FleetNoveltyDetector, get_novelty_feature_columns


class TestInnovationNovelty(unittest.TestCase):
    """Test suite for unsupervised fleet novelty detector."""

    def test_novelty_detector_fit_and_score(self):
        """Verify novelty detector trains on normal data and flags extreme outliers."""
        # 1. Normal synthetic training fleet (100 rows with low reboots, low silence)
        np.random.seed(42)
        normal_data = pd.DataFrame({
            "gateway_id": [f"{i:012x}" for i in range(100)],
            "feat_offline_hours": np.random.exponential(1.0, 100),
            "feat_missing_hours": np.random.exponential(5.0, 100),
            "feat_reboot_cnt_total": np.random.poisson(2.0, 100),
            "feat_mean_load1": np.random.normal(0.8, 0.2, 100),
        })
        feature_cols = ["feat_offline_hours", "feat_missing_hours", "feat_reboot_cnt_total", "feat_mean_load1"]

        detector = FleetNoveltyDetector(contamination=0.1, random_state=42)
        detector.fit(normal_data, feature_cols)
        self.assertTrue(detector.is_fitted_)

        # 2. Test fleet: 1 normal, 1 extreme outlier (reboots = 1500)
        test_data = pd.DataFrame([
            {
                "gateway_id": "000000000001",
                "feat_offline_hours": 1.0,
                "feat_missing_hours": 4.0,
                "feat_reboot_cnt_total": 2,
                "feat_mean_load1": 0.8,
            },
            {
                "gateway_id": "000000000002",
                "feat_offline_hours": 120.0,
                "feat_missing_hours": 150.0,
                "feat_reboot_cnt_total": 1500,
                "feat_mean_load1": 15.0,
            },
        ])

        scores = detector.score_samples(test_data)
        self.assertEqual(len(scores), 2)
        self.assertTrue((scores["feat_novelty_score"] >= 0.0).all())
        self.assertTrue((scores["feat_novelty_score"] <= 1.0).all())

        # Outlier should have higher novelty score and be flagged as anomaly
        self.assertGreater(scores.iloc[1]["feat_novelty_score"], scores.iloc[0]["feat_novelty_score"])
        self.assertEqual(scores.iloc[1]["is_novel_anomaly"], 1)
        self.assertIn(scores.iloc[1]["novelty_primary_driver"], feature_cols)


if __name__ == "__main__":
    unittest.main()
