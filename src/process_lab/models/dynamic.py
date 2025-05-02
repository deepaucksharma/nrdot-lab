"""
Dynamic Cost Model using Histogram Data from NRDB.

This module implements a dynamic cost model for ProcessSample events based on
actual histogram data from NRDB.
"""

import math
import statistics
from typing import Dict, Any, Optional, List, Tuple, Union


def parse_histogram_bucket(bucket_str: str) -> Tuple[float, float]:
    """
    Parse a histogram bucket string into range values.
    
    Args:
        bucket_str: String representation of histogram bucket (e.g. "10.0-20.0")
        
    Returns:
        Tuple of (min, max) values
    """
    try:
        parts = bucket_str.strip().split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid bucket format: {bucket_str}")
            
        return float(parts[0]), float(parts[1])
    except (ValueError, IndexError) as e:
        raise ValueError(f"Could not parse histogram bucket '{bucket_str}': {e}")


def process_histogram_data(histogram_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process histogram data from NRDB.
    
    Args:
        histogram_data: List of histogram data points from NRDB
        
    Returns:
        Processed histogram data
    """
    if not histogram_data:
        return {
            "total_pids": 0,
            "avg_bytes": 0,
            "buckets": {},
            "valid": False,
        }
        
    total_pids = 0
    weighted_bytes = 0
    buckets = {}
    
    for point in histogram_data:
        if "bytes" not in point or "pids" not in point:
            continue
            
        bucket_raw = point["bytes"]
        bucket_dict = {}
        
        if isinstance(bucket_raw, dict):
            bucket_dict = bucket_raw
        elif isinstance(bucket_raw, str):
            # Try to parse JSON string
            import json
            try:
                bucket_dict = json.loads(bucket_raw)
            except json.JSONDecodeError:
                continue
                
        pids = point.get("pids", 0)
        if pids <= 0:
            continue
            
        total_pids += pids
        
        for bucket_str, count in bucket_dict.items():
            buckets[bucket_str] = buckets.get(bucket_str, 0) + count
            bucket_min, bucket_max = parse_histogram_bucket(bucket_str)
            bucket_mid = (bucket_min + bucket_max) / 2
            weighted_bytes += bucket_mid * count
            
    # Calculate average bytes
    avg_bytes = 0
    if total_pids > 0 and sum(buckets.values()) > 0:
        avg_bytes = weighted_bytes / sum(buckets.values())
        
    return {
        "total_pids": total_pids,
        "avg_bytes": avg_bytes,
        "buckets": buckets,
        "valid": total_pids > 0 and avg_bytes > 0,
    }


def estimate_gb_day_from_histogram(
    sample_rate: int,
    keep_ratio: float,
    histogram_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Estimate GB per day using histogram data from NRDB.
    
    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        histogram_data: Histogram data from NRDB
        
    Returns:
        Dictionary with estimation details
    """
    # Process histogram data
    processed = process_histogram_data(histogram_data)
    
    if not processed["valid"]:
        # Return a fallback result
        return {
            "gb_day": 0,
            "confidence": 0.0,
            "method": "histogram",
            "valid": False,
            "reason": "Invalid histogram data",
        }
        
    # Calculate events per day
    events_per_day = (86400 / sample_rate) * processed["total_pids"] * keep_ratio
    
    # Calculate GB per day
    gb_per_day = events_per_day * processed["avg_bytes"] / 1e9
    
    # Calculate confidence based on histogram data quality
    total_samples = sum(processed["buckets"].values())
    confidence = min(0.95, (math.log10(total_samples + 1) / 5))
    
    return {
        "gb_day": gb_per_day,
        "confidence": confidence,
        "method": "histogram",
        "valid": True,
        "stats": {
            "total_pids": processed["total_pids"],
            "avg_bytes": processed["avg_bytes"],
            "total_samples": total_samples,
            "num_buckets": len(processed["buckets"]),
        },
    }


def fetch_histogram_data(
    nrdb_client: Any,
    window: str = "6h",
    entity_name_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch histogram data from NRDB.
    
    Args:
        nrdb_client: NRDB client
        window: Time window for data (default: "6h")
        entity_name_filter: Optional filter for entity name
        
    Returns:
        List of histogram data points
    """
    try:
        # Use paginated query to get complete histogram
        histogram_data = nrdb_client.get_histogram_paginated(
            window=window,
            entity_name_filter=entity_name_filter,
        )
        return histogram_data
    except Exception as e:
        print(f"Error fetching histogram data: {e}")
        return []


def estimate_cost_from_nrdb(
    sample_rate: int,
    keep_ratio: float,
    nrdb_client: Any,
    window: str = "6h",
    entity_name_filter: Optional[str] = None,
    price_per_gb: float = 0.35,
) -> Dict[str, Any]:
    """
    Estimate cost based on histogram data from NRDB.
    
    Args:
        sample_rate: Sample rate in seconds (20-300)
        keep_ratio: Fraction of samples retained after filtering (0.0-1.0)
        nrdb_client: NRDB client
        window: Time window for data (default: "6h")
        entity_name_filter: Optional filter for entity name
        price_per_gb: Price per GB in USD (default: 0.35)
        
    Returns:
        Dictionary with estimation details
    """
    # Fetch histogram data
    histogram_data = fetch_histogram_data(
        nrdb_client=nrdb_client,
        window=window,
        entity_name_filter=entity_name_filter,
    )
    
    # Estimate GB per day
    estimate = estimate_gb_day_from_histogram(
        sample_rate=sample_rate,
        keep_ratio=keep_ratio,
        histogram_data=histogram_data,
    )
    
    # Calculate monthly cost
    gb_day = estimate["gb_day"]
    monthly_cost = gb_day * 30 * price_per_gb
    
    return {
        "gb_day": gb_day,
        "monthly_cost": monthly_cost,
        "confidence": estimate["confidence"],
        "method": "histogram",
        "valid": estimate["valid"],
        "stats": estimate.get("stats", {}),
        "inputs": {
            "sample_rate": sample_rate,
            "keep_ratio": keep_ratio,
            "price_per_gb": price_per_gb,
            "window": window,
        },
    }
