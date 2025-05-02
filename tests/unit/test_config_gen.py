"""Unit tests for the configuration generator."""

import re
import yaml
import pytest
from process_lab.config_gen import (
    render_agent_yaml,
    load_filter_definitions,
    load_wizard_presets,
    generate_config_from_preset,
)


def _strip_ts(content: str) -> str:
    """Remove volatile timestamp comments from YAML."""
    return "\n".join(
        l for l in content.splitlines() if not l.startswith("# Generated")
    )


def test_load_filter_definitions():
    """Test loading filter definitions."""
    filters = load_filter_definitions()
    
    # Check that required filters exist
    assert "standard" in filters
    assert "aggressive" in filters
    
    # Check filter structure
    standard = filters["standard"]
    assert "description" in standard
    assert "patterns" in standard
    assert isinstance(standard["patterns"], dict)
    
    # Check pattern structure
    patterns = standard["patterns"]
    for pattern, value in patterns.items():
        assert isinstance(pattern, str)
        assert isinstance(value, bool)


def test_load_wizard_presets():
    """Test loading wizard presets."""
    presets = load_wizard_presets()
    
    # Check that some presets exist
    assert len(presets) > 0
    
    # Check preset structure
    for name, preset in presets.items():
        assert "description" in preset
        assert "sample_rate" in preset
        assert "filter_type" in preset
        
        # Check sample rate is within valid range
        assert 20 <= preset["sample_rate"] <= 300
        
        # Check filter type is valid
        assert preset["filter_type"] in ["standard", "aggressive", "minimal"]


def test_render_agent_yaml_basic():
    """Test basic YAML rendering."""
    yaml_str = render_agent_yaml(sample_rate=60, filter_type="standard")
    
    # Parse YAML to check structure
    config = yaml.safe_load(yaml_str)
    
    # Check required fields
    assert config["metrics_process_sample_rate"] == 60
    assert "exclude_matching_metrics" in config
    assert isinstance(config["exclude_matching_metrics"], dict)
    assert config["collect_command_line"] is False


def test_render_agent_yaml_with_overrides():
    """Test YAML rendering with overrides."""
    overrides = {
        "collect_command_line": True,
        "log_file": "/var/log/newrelic-infra.log",
    }
    
    yaml_str = render_agent_yaml(
        sample_rate=120,
        filter_type="aggressive",
        overrides=overrides,
    )
    
    # Parse YAML to check structure
    config = yaml.safe_load(yaml_str)
    
    # Check overrides were applied
    assert config["metrics_process_sample_rate"] == 120
    assert config["collect_command_line"] is True
    assert config["log_file"] == "/var/log/newrelic-infra.log"


def test_render_agent_yaml_invalid_filter():
    """Test rendering with invalid filter type."""
    with pytest.raises(ValueError, match="Unknown filter type"):
        render_agent_yaml(sample_rate=60, filter_type="nonexistent")


@pytest.mark.parametrize("sample_rate,filter_type", [
    (60, "standard"),
    (90, "aggressive"),
    (30, "standard"),
    (300, "aggressive"),
])
def test_render_matches_snapshot(snapshot, sample_rate, filter_type):
    """Test that rendered YAML matches snapshots."""
    rendered = render_agent_yaml(sample_rate=sample_rate, filter_type=filter_type)
    # Remove timestamp for stable snapshots
    stable_content = _strip_ts(rendered)
    snapshot.assert_match(stable_content, f"{filter_type}-{sample_rate}.yml")


def test_generate_config_from_preset():
    """Test generating config from a preset."""
    yaml_str = generate_config_from_preset("web_standard")
    
    # Parse YAML to check structure
    config = yaml.safe_load(yaml_str)
    
    # Check that preset values were applied
    assert config["metrics_process_sample_rate"] == 90
    assert config["exclude_matching_metrics"]["process.nginx.*"] is False
    assert config["exclude_matching_metrics"]["process.node.*"] is False


def test_generate_config_from_preset_invalid():
    """Test generating config with invalid preset name."""
    with pytest.raises(ValueError, match="Unknown preset"):
        generate_config_from_preset("nonexistent")
