"""
Cost estimation for New Relic Infrastructure ProcessSample events.

This module provides a unified interface for estimating data volume and cost
for ProcessSample events in New Relic.
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import yaml

from ..models.static import estimate_gb_day as static_gb_day
from ..models.static import estimate_cost as static_cost
from ..models.dynamic import estimate_gb_day_from_histogram
from ..models.dynamic import estimate_cost_from_nrdb
from ..models.blended import estimate_cost_blended as _estimate_cost_blended

# Constants
COST_MODEL_STATIC = "static"
COST_MODEL_DYNAMIC = "histogram"
COST_MODEL_BLENDED = "blended"


def estimate_gb_day(
    sample_rate: int,
    keep_ratio: float,
    process_count: Optional[int] = None,
    avg_bytes: Optional[float] = None,
) -> float:
    """
    Estimate GB per day using static heuristics.

    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        process_count: Number of processes (default: 150)
        avg_bytes: Average bytes per event (default: 450.0)

    Returns:
        Estimated GB per day
    """
    return static_gb_day(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        process_count=process_count,
        avg_bytes=avg_bytes
    )


def estimate_cost(
    sample_rate: int,
    keep_ratio: float,
    process_count: Optional[int] = None,
    avg_bytes: Optional[float] = None,
    price_per_gb: float = 0.35,
    model: str = COST_MODEL_STATIC,
    nrdb_client: Optional[Any] = None,
    window: str = "6h",
) -> Dict[str, Any]:
    """
    Estimate cost for a configuration.
    
    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        process_count: Number of processes (default: 150)
        avg_bytes: Average bytes per event (default: 450.0)
        price_per_gb: Price per GB in USD (default: 0.35)
        model: Cost model to use (static, histogram, blended)
        nrdb_client: NRDB client for dynamic models
        window: Time window for dynamic data
        
    Returns:
        Dictionary with estimation details
    """
    if model == COST_MODEL_STATIC or not nrdb_client:
        return static_cost(
            sample_rate=sample_rate,
            keep_ratio=keep_ratio,
            process_count=process_count,
            avg_bytes=avg_bytes,
            price_per_gb=price_per_gb
        )
    elif model == COST_MODEL_DYNAMIC:
        return estimate_cost_from_nrdb(
            sample_rate=sample_rate,
            keep_ratio=keep_ratio,
            nrdb_client=nrdb_client,
            window=window,
            price_per_gb=price_per_gb
        )
    elif model == COST_MODEL_BLENDED:
        return estimate_cost_blended(
            sample_rate=sample_rate,
            keep_ratio=keep_ratio,
            nrdb_client=nrdb_client,
            process_count=process_count,
            avg_bytes=avg_bytes,
            window=window,
            price_per_gb=price_per_gb
        )
    else:
        raise ValueError(f"Unknown cost model: {model}")


def estimate_cost_blended(
    sample_rate: int,
    keep_ratio: float,
    nrdb_client: Optional[Any] = None,
    process_count: Optional[int] = None,
    avg_bytes: Optional[float] = None,
    window: str = "6h",
    entity_name_filter: Optional[str] = None,
    price_per_gb: float = 0.35,
) -> Dict[str, Any]:
    """
    Estimate cost using a blend of static and dynamic models based on confidence.
    
    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        nrdb_client: Optional NRDB client for dynamic model
        process_count: Number of processes for static model (default: 150)
        avg_bytes: Average bytes per event for static model (default: 450.0)
        window: Time window for dynamic data (default: "6h")
        entity_name_filter: Optional filter for entity name
        price_per_gb: Price per GB in USD (default: 0.35)
        
    Returns:
        Dictionary with blended estimation details
    """
    return _estimate_cost_blended(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        nrdb_client=nrdb_client,
        process_count=process_count,
        avg_bytes=avg_bytes,
        window=window,
        entity_name_filter=entity_name_filter,
        price_per_gb=price_per_gb
    )


def estimate_cost_from_config(
    config_path: Path,
    price_per_gb: float = 0.35,
    model: str = COST_MODEL_BLENDED,
    nrdb_client: Optional[Any] = None,
    window: str = "6h",
) -> Dict[str, Any]:
    """
    Estimate cost for a configuration file.
    
    Args:
        config_path: Path to the configuration file
        price_per_gb: Price per GB in USD (default: 0.35)
        model: Cost model to use (static, histogram, blended)
        nrdb_client: NRDB client for dynamic models
        window: Time window for dynamic data
        
    Returns:
        Cost estimation results
    """
    # Load the configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # Extract needed parameters
    sample_rate = config.get("metrics_process_sample_rate", 60)
    
    # Calculate keep ratio from excluded metrics
    # In a real implementation, we'd calculate this from the filter patterns
    # For now, use a default value
    keep_ratio = 0.92  # Default heuristic
    
    # Use the appropriate cost model
    return estimate_cost(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        price_per_gb=price_per_gb,
        model=model,
        nrdb_client=nrdb_client,
        window=window
    )
