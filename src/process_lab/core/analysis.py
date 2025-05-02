"""
Process analysis and recommendation engine.

This module provides functionality to analyze process data from NRDB
and generate recommendations for optimized agent configurations.
"""

import os
from typing import Dict, Any, Optional, List, Tuple, Set, Iterator
from pathlib import Path
import yaml
import json

from . import config as config_module
from . import cost as cost_module
from ..utils import lint


def read_nrql_query(file_path: Path) -> str:
    """
    Read a NRQL query from a file.
    
    Args:
        file_path: Path to the NRQL query file
        
    Returns:
        Query string
    """
    with open(file_path, "r") as f:
        return f.read().strip()


def read_nrql_queries(directory_path: Path) -> Dict[str, str]:
    """
    Load NRQL queries from files in specified directory.
    
    Args:
        directory_path: Directory containing NRQL query files
        
    Returns:
        Dictionary mapping file names to query strings
    """
    queries = {}
    
    if not directory_path.exists():
        return queries
        
    for file_path in directory_path.glob("*.nrql"):
        query_name = file_path.stem
        queries[query_name] = read_nrql_query(file_path)
        
    return queries


def calculate_keep_ratio(
    processes: List[Dict[str, Any]],
    filter_patterns: Dict[str, bool]
) -> float:
    """
    Calculate the keep ratio for a set of processes with given filter patterns.
    
    Args:
        processes: List of process data from NRDB
        filter_patterns: Dictionary mapping filter patterns to exclude flags
        
    Returns:
        Keep ratio as a float between 0.0 and 1.0
    """
    if not processes:
        return 1.0
        
    total_processes = len(processes)
    excluded_processes = 0
    
    for process in processes:
        process_name = process.get("processDisplayName", "")
        if process_name:
            # Create process metric format
            process_metric = f"process.{process_name}.*"
            
            # Check if directly excluded
            if process_metric in filter_patterns and filter_patterns[process_metric]:
                excluded_processes += 1
                continue
                
            # Check for pattern matches
            for pattern, excluded in filter_patterns.items():
                if not excluded:
                    continue
                    
                # Simple pattern matching (can be improved)
                if pattern.endswith("*") and process_metric.startswith(pattern[:-1]):
                    excluded_processes += 1
                    break
                    
                if pattern.startswith("*") and process_metric.endswith(pattern[1:]):
                    excluded_processes += 1
                    break
    
    # Calculate keep ratio
    keep_ratio = 1.0 - (excluded_processes / total_processes)
    
    return max(0.0, min(1.0, keep_ratio))  # Ensure between 0 and 1


def identify_tier1_processes(
    processes: List[Dict[str, Any]],
    prevalence_threshold: float = 0.5
) -> List[str]:
    """
    Identify Tier-1 processes based on prevalence across hosts.
    
    Args:
        processes: List of processes with prevalence data
        prevalence_threshold: Threshold to consider a process as Tier-1 (0.0-1.0)
        
    Returns:
        List of Tier-1 process names
    """
    if not processes:
        return []
        
    # Find maximum host count to calculate prevalence
    max_host_count = 0
    for process in processes:
        host_count = process.get("hostCount", 0)
        max_host_count = max(max_host_count, host_count)
        
    if max_host_count == 0:
        return []
        
    # Identify Tier-1 processes based on prevalence
    tier1_processes = []
    for process in processes:
        process_name = process.get("processDisplayName", "")
        host_count = process.get("hostCount", 0)
        
        # Calculate prevalence
        prevalence = host_count / max_host_count
        
        if prevalence >= prevalence_threshold:
            tier1_processes.append(process_name)
            
    return tier1_processes


def calculate_tier1_coverage(
    tier1_processes: List[str],
    filter_patterns: Dict[str, bool]
) -> Tuple[float, List[str]]:
    """
    Calculate coverage of Tier-1 processes with given filter patterns.
    
    Args:
        tier1_processes: List of Tier-1 process names
        filter_patterns: Dictionary mapping filter patterns to exclude flags
        
    Returns:
        Tuple of (coverage ratio, list of excluded tier1 processes)
    """
    if not tier1_processes:
        return 1.0, []
        
    excluded_tier1 = []
    
    for process_name in tier1_processes:
        # Create process metric format
        process_metric = f"process.{process_name}.*"
        
        # Check if directly excluded
        if process_metric in filter_patterns and filter_patterns[process_metric]:
            excluded_tier1.append(process_name)
            continue
            
        # Check for pattern matches
        for pattern, excluded in filter_patterns.items():
            if not excluded:
                continue
                
            # Simple pattern matching
            if pattern.endswith("*") and process_metric.startswith(pattern[:-1]):
                excluded_tier1.append(process_name)
                break
                
            if pattern.startswith("*") and process_metric.endswith(pattern[1:]):
                excluded_tier1.append(process_name)
                break
    
    # Calculate coverage
    coverage = 1.0 - (len(excluded_tier1) / len(tier1_processes))
    
    return coverage, excluded_tier1


def generate_configuration_variants(
    sample_rates: List[int] = [30, 60, 90, 120, 180],
    filter_types: List[str] = ["standard", "aggressive"]
) -> List[Dict[str, Any]]:
    """
    Generate a list of configuration variants to analyze.
    
    Args:
        sample_rates: List of sample rates to test
        filter_types: List of filter types to test
        
    Returns:
        List of configuration variant dictionaries
    """
    variants = []
    variant_id = 1
    
    # Add standard variations
    for rate in sample_rates:
        for filter_type in filter_types:
            variants.append({
                "id": variant_id,
                "sample_rate": rate,
                "filter_type": filter_type,
                "collect_cmdline": False,
            })
            variant_id += 1
    
    # Add some variants with command line collection
    variants.append({
        "id": variant_id,
        "sample_rate": 60,
        "filter_type": "standard",
        "collect_cmdline": True,
    })
    variant_id += 1
    
    variants.append({
        "id": variant_id,
        "sample_rate": 120,
        "filter_type": "aggressive",
        "collect_cmdline": True,
    })
    
    return variants


def analyze_and_recommend(
    nrdb_client: Any,
    window: str = "7d",
    entity_filter: Optional[str] = None,
    budget_gb_day: Optional[float] = None,
    max_risk_score: Optional[int] = None,
    sample_rates: List[int] = [30, 60, 90, 120, 180],
    filter_types: List[str] = ["standard", "aggressive"],
    price_per_gb: float = 0.35,
) -> List[Dict[str, Any]]:
    """
    Analyze process data and recommend optimal configurations.
    
    Args:
        nrdb_client: NRDB client for queries
        window: Time window for analysis
        entity_filter: Optional filter for entity name/GUID
        budget_gb_day: Maximum GB per day budget
        max_risk_score: Maximum acceptable risk score
        sample_rates: List of sample rates to test
        filter_types: List of filter types to test
        price_per_gb: Price per GB in USD
        
    Returns:
        List of configurations ranked by suitability
    """
    # Generate configuration variants to test
    variants = generate_configuration_variants(sample_rates, filter_types)
    
    # Analyze each variant
    results = []
    
    for variant in variants:
        # Get filter patterns for this filter type
        filters = config_module.load_filter_definitions()
        filter_type = variant["filter_type"]
        
        if filter_type not in filters:
            continue
            
        filter_patterns = filters[filter_type]["patterns"]
        
        # Set up overrides
        overrides = {"collect_command_line": variant["collect_cmdline"]}
        
        # Render the configuration for this variant
        yaml_content = config_module.render_agent_yaml(
            sample_rate=variant["sample_rate"],
            filter_type=filter_type,
            overrides=overrides
        )
        
        # Write temporary config file for analysis
        temp_config_path = Path("./temp_config.yml")
        with open(temp_config_path, "w") as f:
            f.write(yaml_content)
        
        try:
            # Calculate keep ratio
            # In a real implementation, we'd fetch process data from NRDB
            # For now, use a simulated value based on filter type
            keep_ratio = 0.92 if filter_type == "standard" else 0.37
            
            # Estimate cost
            cost_estimate = cost_module.estimate_cost(
                sample_rate=variant["sample_rate"],
                keep_ratio=keep_ratio,
                price_per_gb=price_per_gb,
                model=cost_module.COST_MODEL_STATIC  # Use static model for consistency in testing
            )
            
            # Calculate risk score
            risk_result = lint.lint_config(
                config_path=temp_config_path,
                use_nrdb=False,  # Use static analysis for consistency
            )
            
            # Calculate tier1 impact
            # In a real implementation, we'd query NRDB for actual Tier-1 processes
            # For now, use a simulated value
            tier1_filtered_pct = 3.5 if filter_type == "standard" else 12.8
            
            # Add results
            result = {
                "id": variant["id"],
                "sample_rate": variant["sample_rate"],
                "filter_type": variant["filter_type"],
                "collect_cmdline": variant["collect_cmdline"],
                "est_gb_day": cost_estimate["gb_day"],
                "est_monthly_cost": cost_estimate["monthly_cost"],
                "risk_score": risk_result["risk_score"],
                "keep_ratio": keep_ratio,
                "tier1_filtered_pct": tier1_filtered_pct,
                "description": f"{filter_type.capitalize()} filter with {variant['sample_rate']}s sample rate",
            }
            
            # Apply budget constraint if provided
            if budget_gb_day is not None and cost_estimate["gb_day"] > budget_gb_day:
                continue
                
            # Apply risk constraint if provided
            if max_risk_score is not None and risk_result["risk_score"] > max_risk_score:
                continue
                
            results.append(result)
            
        finally:
            # Clean up temporary file
            if temp_config_path.exists():
                os.remove(temp_config_path)
    
    # Rank results by a score that balances cost and risk
    # Lower score is better
    for result in results:
        # Normalize values to 0-10 scale
        norm_cost = min(10, result["est_gb_day"] * 10)  # Assume 1 GB/day is max ideal
        norm_risk = result["risk_score"]
        norm_tier1 = min(10, result["tier1_filtered_pct"] / 10)  # % to 0-10 scale
        
        # Calculate balanced score (lower is better)
        result["balanced_score"] = (norm_cost * 0.4) + (norm_risk * 0.4) + (norm_tier1 * 0.2)
    
    # Sort by balanced score (lower is better)
    results.sort(key=lambda x: x["balanced_score"])
    
    # Add ranks
    for i, result in enumerate(results):
        result["rank"] = i + 1
    
    return results


def select_best_configuration(
    recommendations: List[Dict[str, Any]],
    prioritize: str = "balanced"  # "cost", "risk", or "balanced"
) -> Dict[str, Any]:
    """
    Select the best configuration from recommendations.
    
    Args:
        recommendations: List of configuration recommendations
        prioritize: What to prioritize (cost, risk, or balanced)
        
    Returns:
        The selected configuration
    """
    if not recommendations:
        return {}
        
    if prioritize == "cost":
        # Sort by estimated cost (lowest first)
        sorted_configs = sorted(recommendations, key=lambda x: x["est_monthly_cost"])
    elif prioritize == "risk":
        # Sort by risk score (lowest first)
        sorted_configs = sorted(recommendations, key=lambda x: x["risk_score"])
    else:  # balanced
        # Use the balanced score we already calculated
        sorted_configs = sorted(recommendations, key=lambda x: x["balanced_score"])
    
    # Return the best configuration
    return sorted_configs[0]


def generate_recommended_config(
    recommendation: Dict[str, Any],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a configuration file from a recommendation.
    
    Args:
        recommendation: Configuration recommendation
        output_path: Path to write the configuration (optional)
        
    Returns:
        Generated YAML configuration
    """
    # Set up configuration parameters
    sample_rate = recommendation["sample_rate"]
    filter_type = recommendation["filter_type"]
    collect_cmdline = recommendation.get("collect_cmdline", False)
    
    # Create overrides
    overrides = {"collect_command_line": collect_cmdline}
    
    # Generate configuration
    yaml_content = config_module.render_agent_yaml(
        sample_rate=sample_rate,
        filter_type=filter_type,
        overrides=overrides
    )
    
    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(yaml_content)
    
    return yaml_content
