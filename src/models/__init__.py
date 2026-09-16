"""Models package for LPDG gateway failure prediction."""

from src.models.target import (
    CANDIDATE_TARGETS,
    DEFAULT_DEFICIT_THRESHOLD,
    DEFAULT_TARGET_NAME,
    build_candidate_targets,
    build_operational_target,
    validate_target_leakage_firewall,
)
from src.models.trainer import (
    ModelEvaluationSummary,
    build_candidate_models,
    evaluate_model_pipeline,
    inspect_model_failure_modes,
    prepare_modeling_dataset,
)

__all__ = [
    "DEFAULT_TARGET_NAME",
    "DEFAULT_DEFICIT_THRESHOLD",
    "CANDIDATE_TARGETS",
    "build_operational_target",
    "build_candidate_targets",
    "validate_target_leakage_firewall",
    "ModelEvaluationSummary",
    "build_candidate_models",
    "prepare_modeling_dataset",
    "evaluate_model_pipeline",
    "inspect_model_failure_modes",
]

