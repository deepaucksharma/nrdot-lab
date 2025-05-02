"""
Common test fixtures and utilities for ZCP tests.

This module provides reusable fixtures, mocks, and helpers for testing
ZCP components consistently across unit and integration tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from zcp_core.bus import Event, EventBus, publish, subscribe
from zcp_preset.model import Preset
from zcp_rollout.models import RolloutResult


@pytest.fixture
def clean_bus():
    """Fixture to ensure a clean event bus for each test."""
    # Import here to avoid circular imports
    from zcp_core.bus import _backend, shutdown
    
    # Clear any existing backend
    global _backend
    _backend = None
    
    # Ensure environment is clean
    os.environ.pop("ZCP_BUS", None)
    
    yield
    
    # Clean up after test
    shutdown()


@pytest.fixture
def event_collector():
    """Fixture that collects events from the bus for verification."""
    events = []
    
    class EventCollector:
        def __init__(self, topic=".*"):
            self.topic = topic
            
        async def handle(self, event: Event) -> None:
            events.append(event)
    
    # Subscribe collector to all events
    collector = EventCollector()
    subscribe(collector)
    
    return events


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_preset():
    """Create a sample preset for testing."""
    return Preset(
        id="test_preset",
        name="Test Preset",
        description="A preset for testing",
        default_sample_rate=15,
        filter_mode="include",
        tier1_patterns=["java", "python", "nodejs"],
        tier2_patterns=["php", "ruby"],
        expected_keep_ratio=0.25,
        avg_bytes_per_sample=2048,
        sha256="test_hash_12345"
    )


@pytest.fixture
def mock_nrdb_client():
    """Mock NRDB client that returns configurable test data."""
    with patch("zcp_validate.validator.NRDBClient") as mock:
        client = mock.return_value
        
        # Default test data
        default_data = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 12.0},
                {"hostname": "host2.example.com", "giBIngested": 10.0}
            ],
            "duration_ms": 150.0
        }
        
        # Configure mock to return test data
        client.query.return_value = default_data
        
        # Add method to customize response
        def set_response(data):
            client.query.return_value = data
        
        client.set_response = set_response
        
        yield client


@pytest.fixture
def mock_rollout_backend():
    """Mock rollout backend with configurable success/failure behavior."""
    mock_backend = MagicMock()
    
    # Default to success
    mock_backend.transfer.return_value = RolloutResult(success=True)
    mock_backend.restart.return_value = RolloutResult(success=True)
    
    # Add method to configure failures
    def configure_failures(host_list=None, failure_message="Mock failure"):
        """Configure specific hosts to fail during rollout."""
        host_list = host_list or []
        
        def mock_transfer(host, content, filepath):
            if host in host_list:
                return RolloutResult(success=False, message=failure_message)
            return RolloutResult(success=True)
        
        def mock_restart(host):
            if host in host_list:
                return RolloutResult(success=False, message=failure_message)
            return RolloutResult(success=True)
        
        mock_backend.transfer.side_effect = mock_transfer
        mock_backend.restart.side_effect = mock_restart
    
    mock_backend.configure_failures = configure_failures
    
    return mock_backend


@pytest.fixture
def mock_jinja_environment():
    """Mock Jinja2 environment for template rendering tests."""
    with patch("zcp_template.renderer.jinja2") as mock_jinja:
        # Create a mock environment
        mock_env = MagicMock()
        mock_jinja.Environment.return_value = mock_env
        
        # Create a mock template that renders based on input
        mock_template = MagicMock()
        
        def render_template(**kwargs):
            """Generate a YAML template based on input tokens."""
            # Basic template with token substitution
            template = """
            integrations:
              - name: nri-process-discovery
                config:
                  interval: {sample_rate}
                  discovery:
                    mode: {filter_mode}
                    match_patterns:
                      {patterns}
            """.format(
                sample_rate=kwargs.get('sample_rate', 15),
                filter_mode=kwargs.get('filter_mode', 'include'),
                patterns="\n                      ".join([f"- {p}" for p in kwargs.get('filter_patterns', [])])
            )
            return template
        
        mock_template.render.side_effect = render_template
        mock_env.get_template.return_value = mock_template
        
        yield mock_jinja


@pytest.fixture
def sample_yaml_config():
    """Return a sample YAML configuration for testing."""
    return """
    integrations:
      - name: nri-process-discovery
        config:
          interval: 15
          discovery:
            mode: include
            match_patterns:
              - java
              - python
              - nodejs
    """


@pytest.fixture
def sample_host_list():
    """Return a sample list of hosts for testing."""
    return [f"host{i}.example.com" for i in range(1, 11)]


class MockError(Exception):
    """Custom error for testing error handling."""
    pass


class SlowOperation:
    """Helper for testing timeouts and performance."""
    
    def __init__(self, delay_seconds=0.1):
        """Initialize with configurable delay."""
        self.delay = delay_seconds
    
    async def execute(self):
        """Execute with delay."""
        import asyncio
        await asyncio.sleep(self.delay)
        return "completed"
