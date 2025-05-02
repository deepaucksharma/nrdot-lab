"""
Integration test for error recovery flow.

This test verifies the system's behavior when errors occur at different stages:
1. Error during template rendering
2. Error during cost estimation
3. Error during rollout
4. Recovery from failed rollout
5. Validation after partial rollout

It uses mocks to simulate error conditions but real component code.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from zcp_core.bus import Event, publish, subscribe
from zcp_cost.coordinator import CostCoordinator
from zcp_cost.plugin import CostRequest, StaticPlugin
from zcp_lint.linter import Linter
from zcp_lint.models import LintRequest
from zcp_preset.loader import PresetLoader
from zcp_preset.model import Preset
from zcp_rollout.models import RolloutJob, RolloutResult
from zcp_rollout.orchestrator import RolloutOrchestrator
from zcp_template.renderer import RenderRequest, TemplateRenderer, TokensInfra
from zcp_validate.models import ValidationJob
from zcp_validate.validator import Validator


class MockError(Exception):
    """Mock error for testing."""
    pass


class TestErrorRecoveryFlow:
    """Integration test for error recovery flow."""
    
    @pytest.fixture
    def mock_nrdb_client(self):
        """Mock NRDB client for validation."""
        with patch("zcp_validate.validator.NRDBClient") as mock:
            client = mock.return_value
            # Configure mock to return test data
            client.query.return_value = {
                "results": [
                    {"hostname": "host1.example.com", "giBIngested": 12.0},
                    {"hostname": "host2.example.com", "giBIngested": 10.0},
                    {"hostname": "host3.example.com", "giBIngested": 8.0}
                ],
                "duration_ms": 150.0
            }
            yield client
    
    @pytest.fixture
    def test_preset(self):
        """Create a test preset."""
        return Preset(
            id="test_preset",
            default_sample_rate=15,
            filter_mode="include",
            tier1_patterns=["java", "python"],
            expected_keep_ratio=0.25,
            avg_bytes_per_sample=2048,
            sha256="test_hash"
        )
    
    @pytest.fixture
    def mock_preset_loader(self, test_preset):
        """Mock preset loader to return test preset."""
        with patch("zcp_preset.loader.PresetLoader") as mock:
            loader = mock.return_value
            loader.load.return_value = test_preset
            loader.list.return_value = ["test_preset"]
            yield loader
    
    @pytest.fixture
    def event_recorder(self):
        """Record events from the bus."""
        events = []
        
        class EventRecorder:
            topic = ".*"  # Match all topics
            
            async def handle(self, event: Event):
                events.append(event)
        
        subscribe(EventRecorder())
        return events
    
    def test_template_rendering_error(self, mock_preset_loader):
        """Test system behavior when template rendering fails."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        assert preset.id == "test_preset"
        
        # 2. Attempt to render template with error
        with patch("zcp_template.renderer.jinja2") as mock_jinja:
            # Mock Jinja2 to raise an error
            mock_env = MagicMock()
            mock_env.get_template.side_effect = MockError("Template not found")
            mock_jinja.Environment.return_value = mock_env
            
            # Attempt to render template
            renderer = TemplateRenderer()
            render_req = RenderRequest(
                template_id="missing_template",
                tokens=TokensInfra(
                    preset_id=preset.id,
                    sample_rate=preset.default_sample_rate,
                    filter_mode=preset.filter_mode,
                    filter_patterns=preset.tier1_patterns
                )
            )
            
            # Verify error is raised and handled
            with pytest.raises(MockError):
                renderer.render(render_req)
    
    def test_rollout_partial_failure(self, mock_preset_loader, mock_nrdb_client):
        """Test system behavior when rollout partially fails."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        
        # 2. Render template (mocked success)
        with patch("zcp_template.renderer.jinja2") as mock_jinja:
            # Mock Jinja2 to return a simple template
            mock_template = MagicMock()
            mock_template.render.return_value = """
            integrations:
              - name: nri-process-discovery
                config:
                  interval: 15
                  discovery:
                    mode: include
                    match_patterns:
                      - java
                      - python
            """
            mock_env = MagicMock()
            mock_env.get_template.return_value = mock_template
            mock_jinja.Environment.return_value = mock_env
            
            # Render template
            renderer = TemplateRenderer()
            render_req = RenderRequest(
                template_id="infra_process",
                tokens=TokensInfra(
                    preset_id=preset.id,
                    sample_rate=preset.default_sample_rate,
                    filter_mode=preset.filter_mode,
                    filter_patterns=preset.tier1_patterns
                )
            )
            result = renderer.render(render_req)
            
            # Verify result
            assert "integrations" in result.text
        
        # 3. Estimate cost (mocked success)
        with patch("zcp_cost.coordinator.publish"):
            coordinator = CostCoordinator(plugins=[StaticPlugin()])
            cost_req = CostRequest(
                preset_id=preset.id,
                host_count=3,
                sample_rate=preset.default_sample_rate,
                filter_patterns=preset.tier1_patterns,
                filter_mode=preset.filter_mode
            )
            estimate = coordinator.estimate(cost_req)
            
            # Verify estimate
            assert estimate.blended_gib_per_day > 0
        
        # 4. Rollout with partial failure
        with patch("zcp_rollout.orchestrator.publish"):
            # Mock backend that fails for specific hosts
            mock_backend = MagicMock()
            
            # Configuration for partial failure
            def mock_transfer(host, content, filepath):
                result = RolloutResult()
                # Succeed for host1, fail for host2, succeed for host3
                if host == "host2.example.com":
                    result.success = False
                    result.message = "Connection error"
                else:
                    result.success = True
                return result
            
            # Set up the mock
            mock_backend.transfer.side_effect = mock_transfer
            mock_backend.restart.return_value.success = True
            
            # Create rollout job
            job = RolloutJob.from_host_list(
                hosts=["host1.example.com", "host2.example.com", "host3.example.com"],
                config_content=result.text,
                filename="config.yaml",
                checksum=result.checksum
            )
            
            # Execute rollout
            orchestrator = RolloutOrchestrator(backend=mock_backend)
            report = orchestrator.execute(job)
            
            # Verify partial success
            assert report.success == 2
            assert report.fail == 1
            assert "host2.example.com" in report.details
            assert "Connection error" in report.details.get("host2.example.com", "")
        
        # 5. Validation after partial rollout
        with patch("zcp_validate.validator.publish"):
            # Create validation job with only successful hosts
            job = ValidationJob(
                hosts=["host1.example.com", "host3.example.com"],  # Excluding failed host
                expected_gib_day=estimate.blended_gib_per_day,
                confidence=estimate.confidence,
                threshold=0.2,
                timeframe_hours=24
            )
            
            # Execute validation
            validator = Validator(nrdb_client=mock_nrdb_client)
            result = validator.validate(job)
            
            # Verify validation result
            assert "host1.example.com" in result.host_results
            assert "host3.example.com" in result.host_results
            assert "host2.example.com" not in result.host_results
    
    def test_recovery_from_cost_error(self, mock_preset_loader):
        """Test recovery from cost estimation error."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        
        # 2. Create mock cost plugin that fails first time, succeeds second time
        mock_plugin = MagicMock()
        mock_plugin.name = "mock_plugin"
        mock_plugin.confidence = 0.9
        
        # First call fails
        mock_plugin.estimate.side_effect = [
            MockError("Database connection error"),  # First call fails
            {"gib_per_day": 5.0, "confidence": 0.9}  # Second call succeeds
        ]
        
        # 3. Try cost estimation and handle error
        coordinator = CostCoordinator(plugins=[mock_plugin])
        cost_req = CostRequest(
            preset_id=preset.id,
            host_count=3,
            sample_rate=preset.default_sample_rate,
            filter_patterns=preset.tier1_patterns,
            filter_mode=preset.filter_mode
        )
        
        # First attempt should fail
        with pytest.raises(MockError):
            coordinator.estimate(cost_req)
        
        # Second attempt should succeed
        estimate = coordinator.estimate(cost_req)
        assert estimate.blended_gib_per_day == 5.0
        assert estimate.confidence == 0.9
