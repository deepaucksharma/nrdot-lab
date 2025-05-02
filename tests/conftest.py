"""Common test fixtures and configuration."""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def mock_env():
    """Set mock environment variables for testing."""
    old_env = os.environ.copy()
    os.environ["NEW_RELIC_API_KEY"] = "test_api_key"
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file."""
    temp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
    yield Path(temp.name)
    # Clean up
    if Path(temp.name).exists():
        Path(temp.name).unlink()


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Return a sample configuration for testing."""
    return {
        "metrics_process_sample_rate": 60,
        "exclude_matching_metrics": {
            "process.chrome.*": True,
            "process.firefox.*": True,
            "process.slack.*": True,
        },
        "collect_command_line": False,
        "log_file": "/var/log/newrelic-infra.log",
    }


@pytest.fixture
def sample_high_risk_config() -> Dict[str, Any]:
    """Return a high-risk configuration for testing."""
    return {
        "metrics_process_sample_rate": 10,
        "exclude_matching_metrics": {
            "process.*": True,
        },
        "collect_command_line": True,
    }


@pytest.fixture
def create_config_file(temp_yaml_file):
    """Create a YAML configuration file with specific content."""
    def _create_file(config):
        with open(temp_yaml_file, "w") as f:
            yaml.dump(config, f)
        return temp_yaml_file
    return _create_file


@pytest.fixture
def vcr_config():
    """Configure VCR for API interaction testing."""
    return {
        "filter_headers": ["Api-Key", "api-key"],
        "filter_query_parameters": ["key", "api_key"],
    }
