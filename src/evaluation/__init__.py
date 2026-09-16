"""Evaluation package for LPDG gateway failure prediction."""

from src.evaluation.cost_simulator import (
    COST_PER_UNVISITED_FAULT_WEEK,
    COST_PER_VISIT,
    OperationalCostResult,
    run_baseline_3sigma_strategy,
    run_random_dispatch_strategy,
    simulate_operational_cost,
)
from src.evaluation.splitters import (
    get_gateway_disjoint_splits,
    get_temporal_walk_forward_splits,
)

__all__ = [
    "COST_PER_VISIT",
    "COST_PER_UNVISITED_FAULT_WEEK",
    "OperationalCostResult",
    "simulate_operational_cost",
    "run_baseline_3sigma_strategy",
    "run_random_dispatch_strategy",
    "get_temporal_walk_forward_splits",
    "get_gateway_disjoint_splits",
]

