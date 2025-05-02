"""
Blended Cost Model combining static and dynamic approaches.

This module implements a blended cost model for ProcessSample events,
combining both static heuristics and dynamic histogram data for
more accurate estimations.
"""

from typing import Dict, Any, Optional, List, Union
import statistics
from . import static
from . import dynamic


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
    # Get static model estimate
    static_est = static.estimate_cost(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        process_count=process_count,
        avg_bytes=avg_bytes,
        price_per_gb=price_per_gb,
    )
    
    # Default to static model
    result = {
        "gb_day": static_est["gb_day"],
        "monthly_cost": static_est["monthly_cost"],
        "confidence": static_est["confidence"],
        "method": "static",
        "models": {
            "static": static_est,
        },
        "inputs": {
            "sample_rate": sample_rate,
            "keep_ratio": keep_ratio,
            "price_per_gb": price_per_gb,
        },
    }
    
    # If NRDB client is provided, add dynamic model
    if nrdb_client:
        try:
            # Get histogram data
            histogram_data = dynamic.fetch_histogram_data(
                nrdb_client=nrdb_client,
                window=window,
                entity_name_filter=entity_name_filter,
            )
            
            # Get dynamic model estimate
            dynamic_est = dynamic.estimate_gb_day_from_histogram(
                sample_rate=sample_rate,
                keep_ratio=keep_ratio,
                histogram_data=histogram_data,
            )
            
            # Calculate monthly cost
            dynamic_est["monthly_cost"] = dynamic_est["gb_day"] * 30 * price_per_gb
            
            # Add to result
            result["models"]["histogram"] = dynamic_est
            
            # If histogram data is valid, blend models based on confidence
            if dynamic_est["valid"]:
                # Determine which model to use as the primary estimate
                if dynamic_est["confidence"] >= static_est["confidence"]:
                    # Dynamic model is more confident
                    result["gb_day"] = dynamic_est["gb_day"]
                    result["monthly_cost"] = dynamic_est["monthly_cost"]
                    result["confidence"] = dynamic_est["confidence"]
                    result["method"] = "histogram"
                else:
                    # Weighted blend if confidences are close
                    static_weight = static_est["confidence"]
                    dynamic_weight = dynamic_est["confidence"] * 0.8  # Slightly penalize dynamic
                    
                    total_weight = static_weight + dynamic_weight
                    if total_weight > 0:
                        # Calculate blended values
                        blended_gb_day = (
                            (static_est["gb_day"] * static_weight) +
                            (dynamic_est["gb_day"] * dynamic_weight)
                        ) / total_weight
                        
                        blended_monthly = blended_gb_day * 30 * price_per_gb
                        blended_conf = max(static_est["confidence"], dynamic_est["confidence"]) * 0.95
                        
                        if abs(blended_gb_day - static_est["gb_day"]) / static_est["gb_day"] > 0.5:
                            # If large difference, prefer higher estimate for safety
                            result["gb_day"] = max(static_est["gb_day"], dynamic_est["gb_day"])
                            result["monthly_cost"] = max(static_est["monthly_cost"], dynamic_est["monthly_cost"])
                            result["method"] = "max_blend"
                        else:
                            # Otherwise use weighted blend
                            result["gb_day"] = blended_gb_day
                            result["monthly_cost"] = blended_monthly
                            result["method"] = "weighted_blend"
                            
                        result["confidence"] = blended_conf
                            
                # Add detailed stats about the blend
                result["blend_details"] = {
                    "static_weight": static_est["confidence"],
                    "dynamic_weight": dynamic_est["confidence"],
                    "dynamic_valid": dynamic_est["valid"],
                    "deviation": abs(dynamic_est["gb_day"] - static_est["gb_day"]) / max(0.001, static_est["gb_day"]),
                }
                
        except Exception as e:
            # Log error but continue with static model
            print(f"Error in dynamic cost estimation: {e}")
            result["dynamic_error"] = str(e)
    
    return result


def estimate_tier_cost_impact(
    tier_breakdown: Dict[str, float],
    price_per_gb: float = 0.35,
) -> Dict[str, Any]:
    """
    Estimate cost impact for different tiers of data.
    
    Args:
        tier_breakdown: Dictionary mapping tiers to GB per day
        price_per_gb: Price per GB in USD
        
    Returns:
        Dictionary with cost impact details by tier
    """
    result = {
        "total_gb_day": sum(tier_breakdown.values()),
        "total_monthly_cost": sum(tier_breakdown.values()) * 30 * price_per_gb,
        "tiers": {},
    }
    
    for tier, gb_day in tier_breakdown.items():
        monthly_cost = gb_day * 30 * price_per_gb
        percentage = gb_day / max(0.001, result["total_gb_day"]) * 100
        
        result["tiers"][tier] = {
            "gb_day": gb_day,
            "monthly_cost": monthly_cost,
            "percentage": percentage,
        }
    
    return result
