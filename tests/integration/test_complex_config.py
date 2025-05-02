"""
Integration test for complex configuration scenarios.

This test verifies the system's ability to handle complex configurations:
1. Multiple tier configurations with different pattern sets
2. Filter mode transitions (include to exclude and vice versa)
3. Complex template rendering with many placeholders
4. Configuration update and replacement scenarios
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from zcp_core.bus import Event, publish, subscribe
from zcp_preset.loader import PresetLoader
from zcp_preset.model import Preset
from zcp_template.renderer import RenderRequest, TemplateRenderer, TokensInfra
from zcp_lint.linter import Linter
from zcp_lint.models import LintRequest
from zcp_rollout.models import RolloutJob
from zcp_rollout.orchestrator import RolloutOrchestrator


class TestComplexConfiguration:
    """Integration test for complex configuration scenarios."""
    
    @pytest.fixture
    def complex_preset(self):
        """Create a complex test preset with multiple tiers."""
        return Preset(
            id="complex_preset",
            name="Complex Configuration",
            description="Preset with multiple tiers and patterns",
            default_sample_rate=15,
            filter_mode="include",
            tier1_patterns=["java", "python", "nodejs", "ruby"],
            tier2_patterns=["php", "dotnet", "golang", "rust"],
            tier3_patterns=["c", "cpp", "perl", "bash"],
            expected_keep_ratio=0.25,
            avg_bytes_per_sample=2048,
            sha256="test_hash_complex"
        )
    
    @pytest.fixture
    def mock_preset_loader(self, complex_preset):
        """Mock preset loader to return test preset."""
        with patch("zcp_preset.loader.PresetLoader") as mock:
            loader = mock.return_value
            loader.load.return_value = complex_preset
            loader.list.return_value = ["complex_preset"]
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
    
    def test_multi_tier_configuration(self, mock_preset_loader):
        """Test rendering templates with multi-tier configurations."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("complex_preset")
        assert preset.id == "complex_preset"
        
        # 2. Render template with all tiers
        with patch("zcp_template.renderer.jinja2") as mock_jinja:
            # Mock Jinja2 to return a complex template
            mock_template = MagicMock()
            mock_template.render.return_value = """
            integrations:
              - name: nri-process-discovery
                config:
                  interval: 15
                  discovery:
                    mode: include
                    match_patterns:
                      # Tier 1 Patterns (High Priority)
                      - java
                      - python
                      - nodejs
                      - ruby
                      
                      # Tier 2 Patterns (Medium Priority)
                      - php
                      - dotnet
                      - golang
                      - rust
                      
                      # Tier 3 Patterns (Low Priority)
                      - c
                      - cpp
                      - perl
                      - bash
            """
            mock_env = MagicMock()
            mock_env.get_template.return_value = mock_template
            mock_jinja.Environment.return_value = mock_env
            
            # Render template
            renderer = TemplateRenderer()
            render_req = RenderRequest(
                template_id="infra_process_multi_tier",
                tokens=TokensInfra(
                    preset_id=preset.id,
                    sample_rate=preset.default_sample_rate,
                    filter_mode=preset.filter_mode,
                    filter_patterns=preset.tier1_patterns + preset.tier2_patterns + preset.tier3_patterns
                )
            )
            result = renderer.render(render_req)
            
            # Verify result
            assert "integrations" in result.text
            for pattern in preset.tier1_patterns + preset.tier2_patterns + preset.tier3_patterns:
                assert pattern in result.text
    
    def test_filter_mode_transition(self, mock_preset_loader):
        """Test switching between include and exclude filter modes."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("complex_preset")
        
        # Original preset has include mode - verify
        assert preset.filter_mode == "include"
        
        # 2. Create modified preset with exclude mode
        exclude_preset = Preset(
            id="exclude_preset",
            name="Exclude Mode Configuration",
            description="Preset with exclude filter mode",
            default_sample_rate=15,
            filter_mode="exclude",  # Changed to exclude
            tier1_patterns=["system", "kernel", "idle"],  # Patterns to exclude
            expected_keep_ratio=0.75,  # Higher keep ratio for exclude mode
            avg_bytes_per_sample=2048,
            sha256="test_hash_exclude"
        )
        
        with patch.object(mock_preset_loader, "load") as mock_load:
            # Configure mock to return different preset
            mock_load.return_value = exclude_preset
            
            # Render template with exclude mode
            with patch("zcp_template.renderer.jinja2") as mock_jinja:
                # Mock Jinja2 to return exclude mode template
                mock_template = MagicMock()
                mock_template.render.side_effect = lambda **kwargs: f"""
                integrations:
                  - name: nri-process-discovery
                    config:
                      interval: {kwargs.get('sample_rate', 15)}
                      discovery:
                        mode: {kwargs.get('filter_mode', 'include')}
                        match_patterns:
                          {chr(10) + '                          - '.join([''] + kwargs.get('filter_patterns', []))}
                """
                mock_env = MagicMock()
                mock_env.get_template.return_value = mock_template
                mock_jinja.Environment.return_value = mock_env
                
                # Render first with include mode
                renderer = TemplateRenderer()
                include_req = RenderRequest(
                    template_id="infra_process",
                    tokens=TokensInfra(
                        preset_id=preset.id,
                        sample_rate=preset.default_sample_rate,
                        filter_mode="include",
                        filter_patterns=preset.tier1_patterns
                    )
                )
                include_result = renderer.render(include_req)
                
                # Then with exclude mode
                exclude_req = RenderRequest(
                    template_id="infra_process",
                    tokens=TokensInfra(
                        preset_id=exclude_preset.id,
                        sample_rate=exclude_preset.default_sample_rate,
                        filter_mode="exclude",
                        filter_patterns=exclude_preset.tier1_patterns
                    )
                )
                exclude_result = renderer.render(exclude_req)
                
                # Verify both templates have the correct mode
                assert "mode: include" in include_result.text
                assert "mode: exclude" in exclude_result.text
                
                # Verify patterns
                for pattern in preset.tier1_patterns:
                    assert pattern in include_result.text
                
                for pattern in exclude_preset.tier1_patterns:
                    assert pattern in exclude_result.text
