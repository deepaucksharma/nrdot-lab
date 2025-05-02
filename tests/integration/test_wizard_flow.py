"""
Integration test for the full wizard flow.

This test exercises the complete flow from:
1. Loading a preset
2. Rendering a template
3. Estimating cost
4. Linting the configuration
5. Rolling out (with a mock backend)
6. Validating the configuration

It uses mocks for external dependencies but real component code.
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
from zcp_rollout.models import RolloutJob
from zcp_rollout.orchestrator import RolloutOrchestrator
from zcp_template.renderer import RenderRequest, TemplateRenderer, TokensInfra
from zcp_validate.models import ValidationJob
from zcp_validate.validator import Validator


class TestWizardFlow:
    """Integration test for the full wizard flow."""
    
    @pytest.fixture
    def mock_nrdb_client(self):
        """Mock NRDB client for validation."""
        with patch("zcp_validate.validator.NRDBClient") as mock:
            client = mock.return_value
            # Configure mock to return test data
            client.query.return_value = {
                "results": [
                    {"hostname": "host1.example.com", "giBIngested": 12.0},
                    {"hostname": "host2.example.com", "giBIngested": 10.0}
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
    
    def test_full_wizard_flow(self, mock_preset_loader, mock_nrdb_client, event_recorder):
        """Test the full wizard flow."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        assert preset.id == "test_preset"
        
        # 2. Render template
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
            assert result.checksum is not None
        
        # 3. Estimate cost
        with patch("zcp_cost.coordinator.publish"):
            coordinator = CostCoordinator(plugins=[StaticPlugin()])
            cost_req = CostRequest(
                preset_id=preset.id,
                host_count=2,
                sample_rate=preset.default_sample_rate,
                filter_patterns=preset.tier1_patterns,
                filter_mode=preset.filter_mode
            )
            estimate = coordinator.estimate(cost_req)
            
            # Verify estimate
            assert estimate.blended_gib_per_day > 0
            assert estimate.confidence > 0
        
        # 4. Lint the configuration
        with patch("zcp_lint.linter.publish"):
            linter = Linter()
            lint_req = LintRequest(content=result.text, filename="config.yaml")
            lint_result = linter.lint(lint_req)
            
            # Verify lint result
            assert lint_result.error_count == 0  # Should be valid YAML
        
        # 5. Rollout the configuration
        with patch("zcp_rollout.orchestrator.publish"):
            # Mock backend that always succeeds
            mock_backend = MagicMock()
            mock_backend.transfer.return_value.success = True
            mock_backend.restart.return_value.success = True
            
            # Create rollout job
            job = RolloutJob.from_host_list(
                hosts=["host1.example.com", "host2.example.com"],
                config_content=result.text,
                filename="config.yaml",
                checksum=result.checksum
            )
            
            # Execute rollout
            orchestrator = RolloutOrchestrator(backend=mock_backend)
            report = orchestrator.execute(job)
            
            # Verify rollout success
            assert report.success == 2
            assert report.fail == 0
        
        # 6. Validate the configuration
        with patch("zcp_validate.validator.publish"):
            # Create validation job
            job = ValidationJob(
                hosts=["host1.example.com", "host2.example.com"],
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
            assert "host2.example.com" in result.host_results
        
        # 7. Verify events were published for each step
        event_topics = [e.topic for e in event_recorder]
        assert "preset.loaded" in event_topics
        assert "template.rendered" in event_topics
        assert "cost.estimated" in event_topics
        assert "lint.finished" in event_topics
        assert "rollout.completed" in event_topics
        assert "validate.result" in event_topics
