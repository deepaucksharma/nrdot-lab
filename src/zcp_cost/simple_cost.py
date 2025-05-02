"""
Simplified cost estimation implementation.

This module provides a direct calculation of data ingest costs
without the complexity of multiple plugins or confidence blending.
"""

import logging
from typing import List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CostRequest(BaseModel):
    """
    Request for cost estimation.
    """
    preset_id: str
    host_count: int
    sample_rate: int
    filter_patterns: List[str]
    filter_mode: str

class CostEstimate(BaseModel):
    """
    Combined cost estimate.
    """
    gib_per_day: float
    description: Optional[str] = None
    
    class Config:
        extra = "forbid"

def estimate_cost(req: CostRequest) -> CostEstimate:
    """
    Estimate data ingest cost using a simple calculation.
    
    This function:
    1. Loads the preset configuration
    2. Calculates daily data ingest based on host count and sampling rate
    3. Returns a simple estimate without confidence blending
    
    Args:
        req: Cost estimation request with preset ID, host count, and sampling details
            
    Returns:
        Simple cost estimate
    """
    from zcp_preset.loader import PresetLoader
    
    # Load the preset
    loader = PresetLoader()
    preset = loader.load(req.preset_id)
    
    # Calculate daily ingest in bytes
    bytes_per_day = (
        req.host_count *                   # Number of hosts
        preset.avg_bytes_per_sample *      # Bytes per sample
        (86400 / req.sample_rate) *        # Samples per day
        preset.expected_keep_ratio         # Ratio of processes that match filter
    )
    
    # Convert to GiB
    gib_per_day = bytes_per_day / (1024 * 1024 * 1024)
    
    # Create a simple estimate
    result = CostEstimate(
        gib_per_day=gib_per_day,
        description=f"Based on {req.host_count} hosts with {req.sample_rate}s sampling rate"
    )
    
    logger.info(f"Estimated cost: {gib_per_day:.2f} GiB per day")
    
    return result
