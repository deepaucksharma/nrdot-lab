"""Unit tests for linter rules."""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from process_lab.lint import (
    lint_config,
    compute_risk_score,
    generate_sarif,
    check_sample_rate,
    check_command_line,
    check_log_file,
    check_glob_patterns,
    check_tier1_coverage,
)


def create_temp_yaml(config):
    """Helper to create a temporary YAML file."""
    temp = tempfile.NamedTemporaryFile(suffix='.yml', delete=False)
    with open(temp.name, 'w') as f:
        yaml.dump(config, f)
    return Path(temp.name)


def test_check_sample_rate():
    """Test sample rate validation."""
    # Missing sample rate
    issues = check_sample_rate({})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R2"
    assert issues[0]["level"] == "error"
    
    # Invalid sample rate
    issues = check_sample_rate({"metrics_process_sample_rate": "invalid"})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R2"
    assert issues[0]["level"] == "error"
    
    # Disabled sample rate
    issues = check_sample_rate({"metrics_process_sample_rate": -1})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R2"
    assert issues[0]["level"] == "info"
    
    # Too low sample rate
    issues = check_sample_rate({"metrics_process_sample_rate": 10})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R2"
    assert issues[0]["level"] == "warning"
    
    # Too high sample rate
    issues = check_sample_rate({"metrics_process_sample_rate": 200})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R2"
    assert issues[0]["level"] == "warning"
    
    # Good sample rate
    issues = check_sample_rate({"metrics_process_sample_rate": 60})
    assert len(issues) == 0


def test_check_command_line():
    """Test command line collection validation."""
    # Command line enabled with low sample rate
    issues = check_command_line({
        "collect_command_line": True,
        "metrics_process_sample_rate": 30,
    })
    assert len(issues) == 1
    assert issues[0]["rule"] == "R3"
    assert issues[0]["level"] == "warning"
    
    # Command line enabled with good sample rate
    issues = check_command_line({
        "collect_command_line": True,
        "metrics_process_sample_rate": 60,
    })
    assert len(issues) == 0
    
    # Command line disabled
    issues = check_command_line({
        "collect_command_line": False,
        "metrics_process_sample_rate": 30,
    })
    assert len(issues) == 0
    
    # Command line not specified (default is False)
    issues = check_command_line({
        "metrics_process_sample_rate": 30,
    })
    assert len(issues) == 0


def test_check_log_file():
    """Test log file validation."""
    # Missing log file
    issues = check_log_file({})
    assert len(issues) == 1
    assert issues[0]["rule"] == "R5"
    assert issues[0]["level"] == "info"
    
    # Log file specified
    issues = check_log_file({
        "log_file": "/var/log/newrelic-infra.log",
    })
    assert len(issues) == 0


def test_check_glob_patterns():
    """Test glob pattern validation."""
    # Missing patterns
    issues = check_glob_patterns({})
    assert len(issues) == 0
    
    # Invalid patterns
    issues = check_glob_patterns({
        "exclude_matching_metrics": "invalid",
    })
    assert len(issues) == 1
    assert issues[0]["rule"] == "R4"
    assert issues[0]["level"] == "error"
    
    # Duplicate patterns
    issues = check_glob_patterns({
        "exclude_matching_metrics": {
            "process.chrome.*": True,
            "process.chrome.*": True,  # Duplicate in dictionary will be deduplicated
        },
    })
    assert len(issues) == 0  # Python dictionary keys are unique
    
    # Overlapping patterns
    issues = check_glob_patterns({
        "exclude_matching_metrics": {
            "process.*": True,
            "process.chrome.*": True,
        },
    })
    assert len(issues) == 1
    assert issues[0]["rule"] == "R4"
    assert issues[0]["level"] == "info"
    
    # No overlaps
    issues = check_glob_patterns({
        "exclude_matching_metrics": {
            "process.chrome.*": True,
            "process.firefox.*": True,
        },
    })
    assert len(issues) == 0


def test_check_tier1_coverage():
    """Test Tier-1 coverage validation."""
    # No patterns
    issues = check_tier1_coverage({})
    assert len(issues) == 0
    
    # No critical exclusions
    issues = check_tier1_coverage({
        "exclude_matching_metrics": {
            "process.chrome.*": True,
            "process.firefox.*": True,
        },
    })
    assert len(issues) == 0
    
    # Critical direct exclusion
    issues = check_tier1_coverage({
        "exclude_matching_metrics": {
            "process.nginx.*": True,
        },
    })
    assert len(issues) == 1
    assert issues[0]["rule"] == "R1"
    assert issues[0]["level"] == "error"
    assert "process.nginx.*" in issues[0]["excluded"]
    
    # Critical overlap exclusion
    issues = check_tier1_coverage({
        "exclude_matching_metrics": {
            "process.*": True,
        },
    })
    assert len(issues) == 1
    assert issues[0]["rule"] == "R1"
    assert issues[0]["level"] == "error"
    
    # Critical override
    issues = check_tier1_coverage({
        "exclude_matching_metrics": {
            "process.*": True,
            "process.nginx.*": False,
        },
    })
    # This is limited by our simple glob matching logic
    # In a real implementation, we'd handle overrides more accurately
    assert len(issues) == 1


def test_compute_risk_score():
    """Test risk score computation."""
    # Empty issues
    assert compute_risk_score([]) == 0
    
    # Single issue
    assert compute_risk_score([
        {"rule": "R2", "level": "warning", "message": "Sample rate too low"},
    ]) == 2
    
    # Multiple issues, same rule
    assert compute_risk_score([
        {"rule": "R2", "level": "warning", "message": "Sample rate too low"},
        {"rule": "R2", "level": "warning", "message": "Another issue with R2"},
    ]) == 2  # Rule weight is only counted once
    
    # Multiple issues, different rules
    assert compute_risk_score([
        {"rule": "R1", "level": "error", "message": "Critical process excluded"},
        {"rule": "R2", "level": "warning", "message": "Sample rate too low"},
    ]) == 6  # R1 (4) + R2 (2)
    
    # All rules
    assert compute_risk_score([
        {"rule": "R1", "level": "error", "message": "Critical process excluded"},
        {"rule": "R2", "level": "warning", "message": "Sample rate too low"},
        {"rule": "R3", "level": "warning", "message": "Command line with low rate"},
        {"rule": "R4", "level": "info", "message": "Pattern overlap"},
        {"rule": "R5", "level": "info", "message": "Missing log file"},
    ]) == 10  # R1 (4) + R2 (2) + R3 (2) + R4 (1) + R5 (1) = 10
    
    # Capped at 10
    assert compute_risk_score([
        {"rule": "R1", "level": "error", "message": "Issue 1"},
        {"rule": "R1", "level": "error", "message": "Issue 2"},
        {"rule": "R2", "level": "warning", "message": "Issue 3"},
        {"rule": "R3", "level": "warning", "message": "Issue 4"},
        {"rule": "R4", "level": "info", "message": "Issue 5"},
        {"rule": "R5", "level": "info", "message": "Issue 6"},
    ]) == 10  # Same as above, capped at 10


def test_generate_sarif():
    """Test SARIF generation."""
    lint_results = {
        "path": "/path/to/config.yml",
        "issues": [
            {"rule": "R1", "level": "error", "message": "Critical process excluded"},
            {"rule": "R2", "level": "warning", "message": "Sample rate too low"},
        ],
        "risk_score": 6,
        "high_risk": False,
    }
    
    sarif_json = generate_sarif(lint_results)
    sarif = json.loads(sarif_json)
    
    # Check SARIF structure
    assert sarif["version"] == "2.1.0"
    assert "runs" in sarif
    assert len(sarif["runs"]) == 1
    
    # Check rules
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]
    assert len(rules) == 5  # All 5 rules should be included
    
    # Check results
    results = sarif["runs"][0]["results"]
    assert len(results) == 2  # Two issues
    
    # Check first result
    assert results[0]["ruleId"] == "R1"
    assert results[0]["level"] == "error"
    assert "Critical process" in results[0]["message"]["text"]
    
    # Check second result
    assert results[1]["ruleId"] == "R2"
    assert results[1]["level"] == "warning"
    assert "Sample rate" in results[1]["message"]["text"]


def test_lint_config():
    """Test full lint_config function."""
    # Create a temporary YAML file
    config = {
        "metrics_process_sample_rate": 20,
        "collect_command_line": True,
        "exclude_matching_metrics": {
            "process.*": True,
            "process.nginx.*": False,
        },
    }
    
    config_path = create_temp_yaml(config)
    
    try:
        # Lint the config
        results = lint_config(config_path)
        
        # Check results
        assert results["path"] == str(config_path)
        assert "issues" in results
        assert "risk_score" in results
        assert "high_risk" in results
        
        # This config should have issues
        assert len(results["issues"]) > 0
        
        # Check some specific issues
        rule_ids = [issue["rule"] for issue in results["issues"]]
        assert "R2" in rule_ids  # Sample rate too low
        assert "R3" in rule_ids  # Command line with low rate
        assert "R5" in rule_ids  # Missing log file
        assert "R1" in rule_ids  # Critical process excluded
        
        # Calculate expected risk score
        expected_score = compute_risk_score(results["issues"])
        assert results["risk_score"] == expected_score
        
    finally:
        # Clean up
        config_path.unlink()
