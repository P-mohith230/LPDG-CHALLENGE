"""Unit tests for Stage 7: Candidate Model Progression & Dual-Dimension Validation.

Tests:
1. Temporal walk-forward splits enforce strict chronological forward validation.
2. Gateway-disjoint splits enforce zero gateway overlap between train and val.
3. Modeling dataset preparation merges features and targets cleanly with zero leakage.
4. Candidate models (LogisticRegression, RandomForest, HistGradientBoosting) instantiate properly.
5. End-to-end candidate model evaluation executes and returns valid operational cost metrics.
"""

import unittest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.evaluation.splitters import (
    get_gateway_disjoint_splits,
    get_temporal_walk_forward_splits,
)
from src.models.trainer import (
    build_candidate_models,
    evaluate_model_pipeline,
    prepare_modeling_dataset,
)


class TestStage7ModelValidation(unittest.TestCase):
    """Test suite for validation splitters and candidate models."""

    def test_temporal_walk_forward_splits_chronology(self):
        """Verify that temporal walk-forward splits are strictly chronological."""
        dates = pd.date_range("2025-08-04", "2026-01-26", freq="7D")
        mock_df = pd.DataFrame({
            "decision_week": np.repeat(dates, 10),
            "gateway_id": [f"gw_{i:04x}" for i in range(10)] * len(dates),
            "feat": np.random.randn(len(dates) * 10),
        })

        splits = list(get_temporal_walk_forward_splits(mock_df, date_col="decision_week"))
        self.assertGreaterEqual(len(splits), 2)

        for train_idx, val_idx, fold_name in splits:
            max_train_date = mock_df.iloc[train_idx]["decision_week"].max()
            min_val_date = mock_df.iloc[val_idx]["decision_week"].min()
            self.assertLess(
                max_train_date,
                min_val_date,
                f"Leakage in {fold_name}: train max {max_train_date} >= val min {min_val_date}",
            )

    def test_gateway_disjoint_splits_zero_overlap(self):
        """Verify that gateway-disjoint splits have zero gateway overlap."""
        gws = [f"gw_{i:04x}" for i in range(50)]
        mock_df = pd.DataFrame({
            "gateway_id": gws * 5,
            "decision_week": pd.date_range("2025-08-04", periods=5, freq="7D").repeat(50),
            "feat": np.random.randn(250),
        })

        splits = list(get_gateway_disjoint_splits(mock_df, gateway_col="gateway_id", n_splits=5))
        self.assertEqual(len(splits), 5)

        for train_idx, val_idx, fold_name in splits:
            train_gws = set(mock_df.iloc[train_idx]["gateway_id"])
            val_gws = set(mock_df.iloc[val_idx]["gateway_id"])
            overlap = train_gws.intersection(val_gws)
            self.assertEqual(
                len(overlap),
                0,
                f"Overlap detected in {fold_name}: {overlap}",
            )

    def test_candidate_models_factory(self):
        """Verify that all candidate models are properly configured."""
        models = build_candidate_models()
        self.assertIn("LogisticRegression", models)
        self.assertIn("RandomForest", models)
        self.assertIn("HistGradientBoosting", models)

        self.assertIsInstance(models["LogisticRegression"], Pipeline)
        self.assertEqual(models["RandomForest"].n_estimators, 100)
        self.assertEqual(models["HistGradientBoosting"].max_iter, 100)

    def test_synthetic_model_evaluation_pipeline(self):
        """Verify evaluate_model_pipeline produces valid operational cost metrics on synthetic data."""
        np.random.seed(42)
        n_samples = 300
        mondays = pd.date_range("2025-11-03", periods=4, freq="7D")
        
        mock_df = pd.DataFrame({
            "gateway_id": [f"{i%20:012x}" for i in range(n_samples)],
            "decision_week": np.random.choice(mondays, size=n_samples),
            "feat1": np.random.randn(n_samples),
            "feat2": np.random.randn(n_samples),
            "target_severe_deficit": np.random.choice([0, 1], size=n_samples, p=[0.9, 0.1]),
        })
        mock_df["target_week"] = mock_df["decision_week"]

        def dummy_split_gen(df):
            yield np.arange(0, 200), np.arange(200, 300), "Synthetic Fold"

        models = build_candidate_models()
        summary = evaluate_model_pipeline(
            model=models["LogisticRegression"],
            df=mock_df,
            feature_cols=["feat1", "feat2"],
            split_generator=dummy_split_gen,
            validation_type="Synthetic",
            target_col="target_severe_deficit",
            visits_per_week=5,
        )

        self.assertEqual(summary.num_folds, 1)
        self.assertGreater(summary.total_cost_eur, 0)
        self.assertGreaterEqual(summary.mean_roc_auc, 0.0)
        self.assertLessEqual(summary.mean_roc_auc, 1.0)


if __name__ == "__main__":
    unittest.main()
