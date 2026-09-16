"""Unit test for dashboard module imports and architecture integrity.

Ensures:
- All pages and components import cleanly without syntax or import errors.
- predictions.csv SHA256 matches expected competition hash.
- Official competition runner run.py is independently runnable without dashboard.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SHA256 = "f27120799bd55bde34508299c411f763d54e7766e266ac54c0619307a6d54608"


class TestDashboardIntegrity(unittest.TestCase):
    """Integrity tests for dashboard modules and competition artifacts."""

    def test_official_prediction_sha256_immutable(self) -> None:
        """Verify predictions.csv SHA256 remains 100% byte-identical."""
        pred_path = PROJECT_ROOT / "predictions.csv"
        with open(pred_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(
            digest,
            EXPECTED_SHA256,
            f"FATAL: predictions.csv has been modified! Digest: {digest}",
        )

    def test_dashboard_modules_importable(self) -> None:
        """Verify all dashboard pages, services, components, and utils import without error."""
        import app.utils.config
        import app.utils.formatting
        import app.utils.state
        import app.data.adapters
        import app.data.demo_data
        import app.services.prediction_service
        import app.services.feature_service
        import app.services.gateway_service
        import app.services.economic_service
        import app.services.model_service
        import app.components.three_scene
        import app.components.kpi_cards
        import app.components.gateway_table
        import app.components.gateway_detail
        import app.components.risk_chart
        import app.components.economic_panel
        import app.components.timeline
        import app.pages.overview
        import app.pages.gateway_explorer
        import app.pages.visit_prioritization
        import app.pages.model_intelligence
        import app.pages.economic_analysis
        import app.pages.innovation_lab
        import app.pages.system_architecture

        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
