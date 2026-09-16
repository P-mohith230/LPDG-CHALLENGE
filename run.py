"""Universal single-command runner for LPDG 2026 Champion Pipeline (C3).

Executes end-to-end inference using the Promoted Champion C3 Architecture
(Baseline 29 Features + 3 Gateway-Specific Baselines, 2-Week Cooldown,
Deterministic Lexicographical Ranking, Diagnostic Signatures <= 300 chars).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prediction.inference import generate_submission

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LPDG 2026 Champion Dispatch Inference Runner (Candidate C3)"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to custom raw challenge data directory (defaults to ./data or standard search order)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "predictions.csv"),
        help="Output CSV destination (default: predictions.csv)",
    )
    args = parser.parse_args()

    print("Executing LPDG 2026 Champion Pipeline (C3)...")
    print(f"Target destination: {args.output}")
    if args.data:
        print(f"Custom data directory: {args.data}")

    df = generate_submission(
        output_path=args.output,
        custom_data_dir=args.data,
    )
    print(f"Successfully generated predictions.csv with {len(df)} rows across 8 scored weeks.")
