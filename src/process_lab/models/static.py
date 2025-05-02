"""
Static Heuristic Cost Model.

This module implements a static heuristic cost model for ProcessSample events.
"""

from typing import Dict, Any, Optional


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
    # Default values if not provided
    proc_count = process_count if process_count is not None else 150
    bytes_per_event = avg_bytes if avg_bytes is not None else 450.0

    # Baseline events per process at 20s sample rate
    baseline_events_per_process = 4320  # 86400 / 20
    
    # Calculate events per day
    events_per_day = (86400 / sample_rate) * proc_count * keep_ratio
    
    # Calculate GB per day
    gb_per_day = events_per_day * bytes_per_event / 1e9
    
    # Apply safety factor to ensure we're not overly optimistic
    safety_factor = 1.1
    return gb_per_day * safety_factor


def estimate_cost(
    sample_rate: int,
    keep_ratio: float,
    process_count: Optional[int] = None,
    avg_bytes: Optional[float] = None,
    price_per_gb: float = 0.35,
) -> Dict[str, Any]:
    """
    Estimate cost based on GB per day.
    
    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        process_count: Number of processes (default: 150)
        avg_bytes: Average bytes per event (default: 450.0)
        price_per_gb: Price per GB in USD (default: 0.35)
        
    Returns:
        Dictionary with estimation details
    """
    gb_day = estimate_gb_day(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        process_count=process_count,
        avg_bytes=avg_bytes,
    )
    
    monthly_cost = gb_day * 30 * price_per_gb
    
    return {
        "gb_day": gb_day,
        "monthly_cost": monthly_cost,
        "confidence": 0.7,  # Default confidence for static model
        "method": "static",
        "inputs": {
            "sample_rate": sample_rate,
            "keep_ratio": keep_ratio,
            "process_count": process_count or 150,
            "avg_bytes": avg_bytes or 450.0,
            "price_per_gb": price_per_gb,
        },
    }
