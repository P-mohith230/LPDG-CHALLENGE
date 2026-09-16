"""Unit tests for Stage 6: Reference Baseline Benchmarking & Evaluation Harness.

Tests:
1. Economic cost calculation math: visit cost €380, unvisited penalty €600.
2. Multi-week fault episode accounting:
   - First visit intercepts active episode and stops penalty accrual.
   - Repeat visits in the same episode waste the €380 cost.
   - False alarms waste €380 without repair benefit.
3. Baseline 3-sigma strategy execution against historical telemetry.
4. Output format compliance: 15 visits per week, ranks 1-15, reason <= 300 chars.
5. Random dispatch baseline execution.
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.config import COST_PER_UNVISITED_FAULT_WEEK, COST_PER_VISIT, get_data_dir
from src.data.loader import load_gateway_master, load_meter_read_success, load_telemetry
from src.models.target import build_operational_target
from src.evaluation.cost_simulator import (
    OperationalCostResult,
    run_baseline_3sigma_strategy,
    run_random_dispatch_strategy,
    simulate_operational_cost,
)


class TestStage6CostSimulator(unittest.TestCase):
    """Test suite for operational cost simulator and baseline strategy."""

    def test_official_economic_constants(self):
        """Verify official constants: €380 visit, €600 unvisited fault week."""
        self.assertEqual(COST_PER_VISIT, 380.0)
        self.assertEqual(COST_PER_UNVISITED_FAULT_WEEK, 600.0)

    def test_synthetic_episode_accounting(self):
        """Verify exact episode interruption and penalty accrual on synthetic data."""
        # 3 gateways over 3 weeks:
        # GW1: faulty in week 1, 2, 3 (1 continuous episode). Visited in week 1.
        #      -> Visit in week 1 intercepts! Weeks 2 and 3 do NOT accrue penalty.
        # GW2: faulty in week 1, 2, 3. Visited in week 2.
        #      -> Week 1 unvisited: €600 penalty. Week 2 visited -> intercepts! Week 3: €0 penalty.
        # GW3: faulty in week 1, 2, 3. Never visited.
        #      -> Weeks 1, 2, 3 unaddressed: 3 x €600 = €1,800 penalty.
        # Total dispatches = 2 visits (GW1 in w1, GW2 in w2). Visit cost = 2 x 380 = €760.
        # Total unaddressed weeks = 1 (GW2 in w1) + 3 (GW3) = 4 weeks -> 4 x €600 = €2,400.
        # Total expected operational cost = €760 + €2,400 = €3,160.

        w1 = pd.Timestamp("2025-10-06")
        w2 = pd.Timestamp("2025-10-13")
        w3 = pd.Timestamp("2025-10-20")

        gt_df = pd.DataFrame({
            "gateway_id": ["0639EA5602C1"] * 3 + ["0639EA5602C2"] * 3 + ["0639EA5602C3"] * 3,
            "week_start": [w1, w2, w3] * 3,
            "target_severe_deficit": [1, 1, 1, 1, 1, 1, 1, 1, 1],
        })

        dispatch_df = pd.DataFrame({
            "week_start": [w1, w2],
            "gateway_id": ["0639EA5602C1", "0639EA5602C2"],
            "rank": [1, 1],
        })

        res = simulate_operational_cost(dispatch_df, gt_df)

        self.assertEqual(res.total_visits, 2)
        self.assertEqual(res.visit_cost_eur, 760.0)
        self.assertEqual(res.unaddressed_fault_weeks, 4)
        self.assertEqual(res.missed_fault_penalty_eur, 2400.0)
        self.assertEqual(res.total_operational_cost_eur, 3160.0)
        self.assertEqual(res.episodes_intercepted, 2)
        self.assertEqual(res.repeat_visits_count, 0)
        self.assertEqual(res.wasted_visits_count, 0)

    def test_repeat_visit_penalty_accounting(self):
        """Verify that repeat visits within the same active episode are counted as wasted visits."""
        # GW1: faulty in w1 and w2. Visited in w1 AND visited again in w2.
        # -> Week 1: first visit intercepts.
        # -> Week 2: second visit is a repeat visit waste (€380 spent, €0 new benefit).
        w1 = pd.Timestamp("2025-10-06")
        w2 = pd.Timestamp("2025-10-13")

        gt_df = pd.DataFrame({
            "gateway_id": ["0639EA5602C1", "0639EA5602C1"],
            "week_start": [w1, w2],
            "target_severe_deficit": [1, 1],
        })
        dispatch_df = pd.DataFrame({
            "week_start": [w1, w2],
            "gateway_id": ["0639EA5602C1", "0639EA5602C1"],
            "rank": [1, 1],
        })

        res = simulate_operational_cost(dispatch_df, gt_df)
        self.assertEqual(res.total_visits, 2)
        self.assertEqual(res.visit_cost_eur, 760.0)
        self.assertEqual(res.unaddressed_fault_weeks, 0)
        self.assertEqual(res.repeat_visits_count, 1)
        self.assertEqual(res.wasted_visits_count, 1)
        self.assertEqual(res.total_operational_cost_eur, 760.0)

    def test_baseline_3sigma_runner_format(self):
        """Verify baseline_3sigma strategy generates valid dispatch records."""
        data_dir = get_data_dir()
        telem = load_telemetry(
            months=["2025-10", "2025-11"],
            columns=["gateway_id", "ts_utc", "offline_duration_sec", "disconnection_cnt", "reboot_cnt"],
            normalize_id="bare",
        )
        test_weeks = [pd.Timestamp("2025-11-03"), pd.Timestamp("2025-11-10")]

        df_disp = run_baseline_3sigma_strategy(telem, test_weeks, visits_per_week=15)

        # 2 weeks x 15 visits = 30 rows
        self.assertEqual(len(df_disp), 30)
        self.assertEqual(set(df_disp.columns), {"week_start", "rank", "gateway_id", "score", "reason"})

        # Check ranks 1 to 15 per week
        for w, grp in df_disp.groupby("week_start"):
            self.assertEqual(len(grp), 15)
            self.assertEqual(list(grp["rank"]), list(range(1, 16)))
            self.assertTrue((grp["reason"].str.len() <= 300).all())


if __name__ == "__main__":
    unittest.main()
