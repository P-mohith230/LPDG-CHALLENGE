"""Unit tests for Stage 9: Final Submission Pipeline, Official Validator & Reproducibility.

Tests:
1. End-to-end generation produces exactly 120 rows across 8 scored weeks.
2. Output passes official validate_submission.py with exit code 0.
3. Strict determinism: two independent inference runs produce identical byte-for-byte results.
"""

import subprocess
import sys
import unittest
from pathlib import Path
import pandas as pd

from src.prediction.inference import generate_submission
from src.utils.config import (
    PROJECT_ROOT,
    REQUIRED_SUBMISSION_COLUMNS,
    SCORED_WEEKS,
    TOTAL_SUBMISSION_ROWS,
    VISITS_PER_WEEK,
)


class TestStage9FinalSubmission(unittest.TestCase):
    """Test suite for final submission validation and reproducibility."""

    @classmethod
    def setUpClass(cls):
        """Generate official predictions.csv once for testing."""
        cls.submission_file = PROJECT_ROOT / "predictions.csv"
        cls.df = generate_submission(output_path=cls.submission_file)

    def test_exact_row_count_and_columns(self):
        """Verify exactly 120 rows and required columns."""
        self.assertEqual(len(self.df), TOTAL_SUBMISSION_ROWS)
        self.assertEqual(list(self.df.columns), REQUIRED_SUBMISSION_COLUMNS)

    def test_ranks_and_weeks_distribution(self):
        """Verify exactly 15 visits per week, ranks 1 to 15 without gaps or repeats."""
        expected_weeks = [w.strftime("%Y-%m-%d") for w in SCORED_WEEKS]
        self.assertEqual(sorted(self.df["week_start"].unique()), sorted(expected_weeks))

        for week, group in self.df.groupby("week_start"):
            self.assertEqual(len(group), VISITS_PER_WEEK)
            self.assertEqual(sorted(group["rank"].tolist()), list(range(1, VISITS_PER_WEEK + 1)))
            # Zero duplicates in same week
            self.assertEqual(group["gateway_id"].nunique(), VISITS_PER_WEEK)

    def test_reason_length_and_non_empty(self):
        """Verify reason strings are non-empty and <= 300 characters."""
        for reason in self.df["reason"]:
            self.assertGreater(len(reason), 0)
            self.assertLessEqual(len(reason), 300)

    def test_official_validator_exit_code_zero(self):
        """Run official validate_submission.py script and assert exit code 0."""
        validator_script = PROJECT_ROOT / "validate_submission.py"
        if not validator_script.exists():
            validator_script = (
                PROJECT_ROOT
                / "OneDrive_2026-08-31"
                / "Innovation Hub 2026"
                / "validate_submission.py"
            )
        self.assertTrue(validator_script.exists(), f"Validator script not found at {validator_script}")

        cmd = [sys.executable, str(validator_script), str(self.submission_file)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(
            res.returncode,
            0,
            f"Official validator failed with exit code {res.returncode}:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}",
        )
        self.assertIn("OK", res.stdout)

    def test_clean_machine_reproducibility(self):
        """Verify that a second independent run produces byte-identical predictions."""
        second_file = PROJECT_ROOT / "scratch" / "predictions_run2.csv"
        df2 = generate_submission(output_path=second_file)

        pd.testing.assert_frame_equal(self.df, df2)

        content1 = self.submission_file.read_bytes()
        content2 = second_file.read_bytes()
        self.assertEqual(content1, content2, "Byte-level discrepancy detected between independent runs!")


if __name__ == "__main__":
    unittest.main()
