"""
Core functionality for Process-Lab.

This package contains the core business logic and domain models.
"""

from .config import (
    render_agent_yaml,
    generate_config_from_preset,
    list_available_presets,
    list_available_filter_types,
    create_custom_filter,
    get_templates_dir,
)

from .cost import (
    estimate_cost,
    estimate_cost_blended,
    estimate_gb_day,
    COST_MODEL_STATIC,
    COST_MODEL_DYNAMIC,
    COST_MODEL_BLENDED,
)

__all__ = [
    # Configuration
    "render_agent_yaml",
    "generate_config_from_preset",
    "list_available_presets",
    "list_available_filter_types",
    "create_custom_filter",
    "get_templates_dir",
    
    # Cost estimation
    "estimate_cost",
    "estimate_cost_blended",
    "estimate_gb_day",
    "COST_MODEL_STATIC",
    "COST_MODEL_DYNAMIC",
    "COST_MODEL_BLENDED",
]
