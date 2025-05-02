"""Fuzz tests for CLI flags and configuration."""

import pytest
import random
import string
from typer.testing import CliRunner
from process_lab.cli import app
from process_lab.config_gen import render_agent_yaml


def random_string(length=10):
    """Generate a random string."""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


@pytest.mark.parametrize("sample_rate", [
    -1, 0, 1, 19, 301, 1000, 99999,
])
def test_fuzz_invalid_sample_rates(sample_rate):
    """Test invalid sample rates."""
    runner = CliRunner()
    result = runner.invoke(app, [
        "generate-configs",
        "--sample-rate", str(sample_rate),
        "--filter-type", "standard",
    ])
    # The command should exit, but not crash
    assert result.exit_code != 0


@pytest.mark.parametrize("filter_type", [
    "", "unknown", "STANDARD", "AgGreSsIvE", "s t a n d a r d",
    random_string(), "standard;", "aggressive'", "standard --",
])
def test_fuzz_invalid_filter_types(filter_type):
    """Test invalid filter types."""
    runner = CliRunner()
    result = runner.invoke(app, [
        "generate-configs",
        "--sample-rate", "60",
        "--filter-type", filter_type,
    ])
    # The command should exit, but not crash
    assert result.exit_code != 0


@pytest.mark.parametrize("inputs", [
    {"sample_rate": "60", "price_per_gb": "-1"},
    {"sample_rate": "60", "price_per_gb": "0"},
    {"sample_rate": "60", "price_per_gb": "invalid"},
    {"sample_rate": "60", "window": ""},
    {"sample_rate": "60", "window": "invalid"},
    {"sample_rate": "60", "window": "6x"},
])
def test_fuzz_estimate_cost_inputs(inputs):
    """Test invalid estimate-cost inputs."""
    runner = CliRunner()
    args = ["estimate-cost"]
    
    for key, value in inputs.items():
        args.extend([f"--{key.replace('_', '-')}", value])
    
    result = runner.invoke(app, args)
    # The command should exit, but not crash
    assert result.exit_code != 0


def test_fuzz_render_yaml_overrides():
    """Test various random overrides for YAML rendering."""
    # Generate a set of random overrides
    for _ in range(10):
        overrides = {}
        
        # Add random boolean overrides
        for _ in range(random.randint(1, 5)):
            key = random_string()
            overrides[key] = random.choice([True, False])
        
        # Add random string overrides
        for _ in range(random.randint(1, 5)):
            key = random_string()
            overrides[key] = random_string()
        
        # Add random numeric overrides
        for _ in range(random.randint(1, 5)):
            key = random_string()
            overrides[key] = random.randint(1, 1000)
        
        try:
            # This should not crash, though it might raise ValueError for invalid filter type
            yaml_str = render_agent_yaml(
                sample_rate=60,
                filter_type="standard",
                overrides=overrides,
            )
            assert "metrics_process_sample_rate: 60" in yaml_str
        except ValueError:
            # We expect ValueError for invalid inputs
            pass
