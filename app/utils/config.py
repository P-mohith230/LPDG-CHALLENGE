"""Application-wide configuration and theme settings for Streamlit Dashboard.

Strictly imports official constants from src.utils.config to maintain a single source of truth.
Does NOT redefine official constants.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Authoritative configuration imports directly from the frozen pipeline
from src.utils.config import (
    FAULT_COST_WEEKLY_EUR,
    MAX_REASON_CHARS,
    REQUIRED_SUBMISSION_COLUMNS,
    SCORED_WEEKS,
    TOTAL_FIXED_VISIT_BUDGET_EUR,
    TOTAL_SUBMISSION_ROWS,
    VISIT_COST_EUR,
    VISITS_PER_WEEK,
    get_data_dir,
)

# Application Identity & Branding
APP_TITLE = "LPDG Gateway Intelligence"
APP_SUBTITLE = "Operational Decision Support & ML Observability"
APP_ICON = "📡"

# Color Palette (Industrial IoT Operations Center: calm, dark, accessible)
COLORS = {
    "bg_dark": "#0E1117",
    "bg_card": "#1E222D",
    "border": "#2A2E39",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "accent_primary": "#2563EB",  # Industrial blue
    "accent_hover": "#3B82F6",
    "status_low": "#3B82F6",     # Muted slate blue (healthy / low risk p < 0.30)
    "status_medium": "#F59E0B",  # Warm industrial amber (0.30 <= p < 0.70)
    "status_high": "#EF4444",    # Restrained coral crimson (p >= 0.70)
    "dispatched": "#8B5CF6",     # Orbital reticle purple (Top 15 priority)
}

# Operational Risk Bands for 3D and 2D Visualizations
RISK_THRESHOLD_OPERATIONAL = 0.50  # Operational target deficit threshold
RISK_BAND_LOW_MAX = 0.30
RISK_BAND_MED_MAX = 0.70

# Provenance Mapping Constants
PROVENANCE = {
    "official_dispatches": "predictions.csv",
    "challenge_parameters": "src/utils/config.py",
    "c3_features": "src/features/builder.py & src/features/gateway_baseline.py",
    "failure_signatures": "src/intelligence/failure_signatures.py",
    "historical_benchmark": "scratch/innovation_experiment_results.json",
    "gateway_master": "gateway_master.csv",
}
