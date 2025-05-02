"""
Configuration linter and risk assessment.

This module provides validation and risk assessment for New Relic Infrastructure
Agent configurations with dynamic NRDB data integration.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set, Union

# Define risk rules and weights
RISK_RULES = {
    "R1": {
        "id": "R1",
        "description": "Tier-1 coverage drop >10%",
        "weight": 4,
    },
    "R2": {
        "id": "R2",
        "description": "Sample-rate <30s or >180s",
        "weight": 2,
    },
    "R3": {
        "id": "R3",
        "description": "Collect cmdline enabled + rate <60s",
        "weight": 2,
    },
    "R4": {
        "id": "R4",
        "description": "Glob pattern duplicates",
        "weight": 1,
    },
    "R5": {
        "id": "R5",
        "description": "YAML missing log_file",
        "weight": 1,
    },
}


# Default Tier-1 processes for offline mode
DEFAULT_TIER1_PROCESSES = [
    {"processDisplayName": "nginx", "hostCount": 350},
    {"processDisplayName": "java", "hostCount": 320},
    {"processDisplayName": "node", "hostCount": 280},
    {"processDisplayName": "python", "hostCount": 250},
    {"processDisplayName": "ruby", "hostCount": 120},
    {"processDisplayName": "php-fpm", "hostCount": 110},
    {"processDisplayName": "mysqld", "hostCount": 180},
    {"processDisplayName": "postgres", "hostCount": 150},
    {"processDisplayName": "redis-server", "hostCount": 90},
    {"processDisplayName": "mongod", "hostCount": 70},
    {"processDisplayName": "memcached", "hostCount": 65},
    {"processDisplayName": "apache2", "hostCount": 200},
    {"processDisplayName": "httpd", "hostCount": 190},
    {"processDisplayName": "elasticsearch", "hostCount": 80},
    {"processDisplayName": "cassandra", "hostCount": 40},
]


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """
    Load and parse a YAML configuration file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Parsed YAML as a dictionary
        
    Raises:
        ValueError: If the file doesn't exist or isn't valid YAML
    """
    if not path.exists():
        raise ValueError(f"Config file not found: {path}")
        
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            
        if not isinstance(config, dict):
            raise ValueError(f"Invalid YAML: expected a dictionary, got {type(config)}")
            
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")


def check_sample_rate(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check if sample rate is within recommended range.
    
    Args:
        config: Parsed YAML configuration
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check if sample rate key exists
    if "metrics_process_sample_rate" not in config:
        issues.append({
            "rule": "R2",
            "level": "error",
            "message": "Missing metrics_process_sample_rate",
        })
        return issues
        
    sample_rate = config["metrics_process_sample_rate"]
    
    # Check if sample rate is a number
    if not isinstance(sample_rate, (int, float)):
        issues.append({
            "rule": "R2",
            "level": "error",
            "message": f"Sample rate must be a number, got {type(sample_rate)}",
        })
        return issues
        
    # Check if sample rate is negative (which means disabled)
    if sample_rate < 0:
        issues.append({
            "rule": "R2",
            "level": "info",
            "message": "Sample rate is negative, ProcessSample collection is disabled",
        })
        return issues
        
    # Check if sample rate is too low
    if 0 < sample_rate < 30:
        issues.append({
            "rule": "R2",
            "level": "warning",
            "message": f"Sample rate ({sample_rate}s) is below recommended minimum (30s)",
        })
        
    # Check if sample rate is too high
    if sample_rate > 180:
        issues.append({
            "rule": "R2",
            "level": "warning",
            "message": f"Sample rate ({sample_rate}s) is above recommended maximum (180s)",
        })
        
    return issues


def check_command_line(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check if command line collection is enabled with a low sample rate.
    
    Args:
        config: Parsed YAML configuration
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check if collect_command_line key exists and is true
    if config.get("collect_command_line", False) is True:
        # Check if sample rate is low
        sample_rate = config.get("metrics_process_sample_rate", 60)
        
        if 0 < sample_rate < 60:
            issues.append({
                "rule": "R3",
                "level": "warning",
                "message": f"Command line collection enabled with low sample rate ({sample_rate}s)",
            })
            
    return issues


def check_log_file(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check if log_file is specified.
    
    Args:
        config: Parsed YAML configuration
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check if log_file key exists
    if "log_file" not in config:
        issues.append({
            "rule": "R5",
            "level": "info",
            "message": "Missing log_file specification",
        })
        
    return issues


def check_glob_patterns(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check glob patterns for duplicates or overlaps.
    
    Args:
        config: Parsed YAML configuration
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check if exclude_matching_metrics key exists
    if "exclude_matching_metrics" not in config:
        return issues
        
    patterns = config["exclude_matching_metrics"]
    
    # Check if patterns is a dictionary
    if not isinstance(patterns, dict):
        issues.append({
            "rule": "R4",
            "level": "error",
            "message": "exclude_matching_metrics must be a dictionary",
        })
        return issues
        
    # Check for duplicate or overlapping patterns
    pattern_list = list(patterns.keys())
    for i, pattern1 in enumerate(pattern_list):
        for pattern2 in pattern_list[i+1:]:
            # Check for exact duplicates
            if pattern1 == pattern2:
                issues.append({
                    "rule": "R4",
                    "level": "warning",
                    "message": f"Duplicate pattern: {pattern1}",
                })
                continue
                
            # Check for potential overlaps (this is a simple heuristic)
            # A more accurate check would use a glob library
            if pattern1.endswith("*") and pattern2.startswith(pattern1[:-1]):
                issues.append({
                    "rule": "R4",
                    "level": "info",
                    "message": f"Potential pattern overlap: {pattern1} and {pattern2}",
                })
                
            if pattern2.endswith("*") and pattern1.startswith(pattern2[:-1]):
                issues.append({
                    "rule": "R4",
                    "level": "info",
                    "message": f"Potential pattern overlap: {pattern2} and {pattern1}",
                })
                
    return issues


def is_process_excluded(process_name: str, patterns: Dict[str, Any]) -> bool:
    """
    Check if a process is excluded by the filter patterns.
    
    Args:
        process_name: Process name to check
        patterns: Exclusion patterns
        
    Returns:
        True if the process is excluded, False otherwise
    """
    process_metric = f"process.{process_name}.*"
    
    # Direct match
    if process_metric in patterns and patterns[process_metric] is True:
        return True
        
    # Check for overlapping patterns
    for pattern, excluded in patterns.items():
        if not excluded:
            continue
            
        # Simple glob match check
        if pattern.endswith("*"):
            pattern_prefix = pattern[:-1]
            if process_metric.startswith(pattern_prefix):
                return True
                
        elif pattern.startswith("*"):
            pattern_suffix = pattern[1:]
            if process_metric.endswith(pattern_suffix):
                return True
                
    return False


def check_tier1_coverage(
    config: Dict[str, Any], 
    tier1_processes: Optional[List[Dict[str, Any]]] = None,
    threshold: float = 0.1  # 10% threshold
) -> List[Dict[str, Any]]:
    """
    Check Tier-1 process coverage with dynamic data if available.
    
    Args:
        config: Parsed YAML configuration
        tier1_processes: List of Tier-1 processes from NRDB or default
        threshold: Coverage drop threshold for warnings
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check if exclude_matching_metrics key exists
    if "exclude_matching_metrics" not in config:
        return issues
        
    patterns = config["exclude_matching_metrics"]
    
    # Use provided Tier-1 processes or default
    tier1 = tier1_processes or DEFAULT_TIER1_PROCESSES
    
    # Check which critical processes would be excluded
    excluded_critical = []
    excluded_hosts = 0
    total_hosts = 0
    
    for process in tier1:
        process_name = process["processDisplayName"]
        host_count = process.get("hostCount", 0)
        total_hosts += host_count
        
        if is_process_excluded(process_name, patterns):
            excluded_critical.append(process_name)
            excluded_hosts += host_count
    
    # Calculate coverage drop percentage
    coverage_drop = 0.0
    if total_hosts > 0:
        coverage_drop = excluded_hosts / total_hosts
    
    # Report issues if coverage drop exceeds threshold
    if coverage_drop > threshold:
        issues.append({
            "rule": "R1",
            "level": "error",
            "message": f"Tier-1 coverage drop of {coverage_drop:.1%} exceeds threshold ({threshold:.1%})",
            "excluded": excluded_critical,
            "coverage_drop": coverage_drop,
        })
    elif excluded_critical:
        issues.append({
            "rule": "R1",
            "level": "warning",
            "message": f"Some Tier-1 processes excluded: {', '.join(excluded_critical)}",
            "excluded": excluded_critical,
            "coverage_drop": coverage_drop,
        })
        
    return issues


def compute_risk_score(issues: List[Dict[str, Any]]) -> int:
    """
    Compute the overall risk score based on issues.
    
    Args:
        issues: List of issues found during linting
        
    Returns:
        Risk score (0-10)
    """
    # Count the weight for each rule that failed
    rule_weights = {rule["id"]: rule["weight"] for rule in RISK_RULES.values()}
    
    # Sum the weights for each unique rule ID that appears in the issues
    total_weight = 0
    seen_rules = set()
    
    for issue in issues:
        rule_id = issue["rule"]
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            total_weight += rule_weights.get(rule_id, 0)
            
    # Special handling for R1 (Tier-1 coverage)
    # If coverage drop is very high, increase the weight
    for issue in issues:
        if issue["rule"] == "R1" and issue.get("coverage_drop", 0) > 0.25:  # >25% drop
            total_weight += 2  # Additional weight
            break
            
    # Cap the risk score at 10
    return min(total_weight, 10)


def lint_config(
    config_path: Path, 
    use_nrdb: bool = False,
    api_key: Optional[str] = None,
    nrdb_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Lint a New Relic Infrastructure Agent configuration.
    
    Args:
        config_path: Path to the configuration file
        use_nrdb: Whether to use NRDB data for dynamic analysis
        api_key: New Relic API key (only needed if use_nrdb is True)
        nrdb_client: Optional pre-initialized NRDB client
        
    Returns:
        Lint results including issues and risk score
    """
    # Load the configuration
    config = load_yaml_config(config_path)
    
    # Get Tier-1 processes from NRDB if requested
    tier1_processes = None
    if use_nrdb:
        try:
            if nrdb_client is None:
                # Import here to avoid circular dependency
                from ..client.nrdb import NRDBClient
                nrdb_client = NRDBClient(api_key=api_key)
                
            tier1_processes = nrdb_client.get_tier1_processes(window="7d")
        except Exception as e:
            print(f"Warning: Could not get Tier-1 processes from NRDB: {e}")
            print("Falling back to default Tier-1 processes list")
    
    # Run all checks
    issues = []
    issues.extend(check_sample_rate(config))
    issues.extend(check_command_line(config))
    issues.extend(check_log_file(config))
    issues.extend(check_glob_patterns(config))
    issues.extend(check_tier1_coverage(config, tier1_processes))
    
    # Compute risk score
    risk_score = compute_risk_score(issues)
    
    return {
        "path": str(config_path),
        "issues": issues,
        "risk_score": risk_score,
        "high_risk": risk_score >= 7,
        "used_nrdb": use_nrdb and tier1_processes is not None,
    }


def calculate_keep_ratio(
    config: Dict[str, Any],
    process_list: Optional[List[Dict[str, Any]]] = None,
    nrdb_client: Optional[Any] = None,
    window: str = "6h",
) -> float:
    """
    Calculate the keep ratio for the configuration.
    
    Args:
        config: Parsed YAML configuration
        process_list: Optional list of processes (if already fetched)
        nrdb_client: NRDB client for fetching process list if needed
        window: Time window for fetching processes
        
    Returns:
        Keep ratio (0.0 to 1.0)
    """
    # If no process list provided and no NRDB client, use static estimate
    if not process_list and not nrdb_client:
        # Static estimate from historical data
        return 0.92  # Default keep ratio from heuristic
    
    # Get process list from NRDB if not provided
    processes = process_list
    if not processes and nrdb_client:
        try:
            processes = nrdb_client.get_process_list_paginated(window=window)
        except Exception as e:
            print(f"Warning: Could not get process list from NRDB: {e}")
            return 0.92  # Fall back to default on error
    
    # If no processes found, use static estimate
    if not processes:
        return 0.92
    
    # Check if exclude_matching_metrics key exists
    if "exclude_matching_metrics" not in config:
        return 1.0  # Nothing excluded
    
    patterns = config["exclude_matching_metrics"]
    
    # Count excluded and total processes
    total_processes = len(processes)
    excluded_processes = 0
    
    for process in processes:
        process_name = process.get("processDisplayName", "")
        if is_process_excluded(process_name, patterns):
            excluded_processes += 1
    
    # Calculate keep ratio
    if total_processes > 0:
        return 1.0 - (excluded_processes / total_processes)
    else:
        return 1.0


def generate_sarif(lint_results: Dict[str, Any], output_path: Optional[Path] = None) -> str:
    """
    Generate a SARIF (Static Analysis Results Interchange Format) report.
    
    Args:
        lint_results: Results from lint_config
        output_path: Path to write the SARIF file to (optional)
        
    Returns:
        SARIF report as a JSON string
    """
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Infra-Lab Linter",
                        "informationUri": "https://github.com/newrelic/infra-lab",
                        "rules": [RISK_RULES[rule_id] for rule_id in RISK_RULES],
                    }
                },
                "results": [
                    {
                        "ruleId": issue["rule"],
                        "level": {
                            "error": "error",
                            "warning": "warning",
                            "info": "note",
                        }.get(issue["level"], "note"),
                        "message": {
                            "text": issue["message"],
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": lint_results["path"],
                                    },
                                }
                            }
                        ],
                    }
                    for issue in lint_results["issues"]
                ],
            }
        ],
    }
    
    # Convert to JSON string
    sarif_json = json.dumps(sarif, indent=2)
    
    # Write to file if output path provided
    if output_path:
        with open(output_path, "w") as f:
            f.write(sarif_json)
            
    return sarif_json
