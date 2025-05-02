"""
Unit tests for the cost coordinator component.

These tests focus on:
1. Plugin selection and confidence blending
2. Cost estimation accuracy
3. Error handling and fallbacks
4. Edge cases in cost calculation
"""

import re
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from zcp_cost.coordinator import CostCoordinator
from zcp_cost.plugin import CostPlugin, CostRequest, CostResult, StaticPlugin


class TestPlugin(CostPlugin):
    """Test cost plugin with configurable behavior."""
    
    def __init__(self, name: str, confidence: float, gib_per_day: float, 
                 should_fail: bool = False, error_msg: Optional[str] = None):
        self.plugin_name = name
        self.plugin_confidence = confidence
        self.gib_value = gib_per_day
        self.should_fail = should_fail
        self.error_msg = error_msg
        self.called = False
    
    @property
    def name(self) -> str:
        return self.plugin_name
    
    @property
    def confidence(self) -> float:
        return self.plugin_confidence
    
    def estimate(self, request: CostRequest) -> Dict:
        """Estimate cost based on configuration."""
        self.called = True
        
        if self.should_fail:
            if self.error_msg:
                raise ValueError(self.error_msg)
            else:
                raise ValueError("Test plugin failure")
        
        return {
            "gib_per_day": self.gib_value,
            "confidence": self.plugin_confidence
        }


class TestCostCoordinator:
    """Tests for the cost coordinator."""
    
    def test_basic_estimation(self):
        """Test basic cost estimation with a single plugin."""
        # Create a simple plugin
        plugin = TestPlugin("test", 0.8, 5.0)
        
        # Create coordinator with the plugin
        coordinator = CostCoordinator(plugins=[plugin])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Verify results
        assert plugin.called
        assert result.blended_gib_per_day == 5.0
        assert result.confidence == 0.8
        assert result.plugin_results[0].plugin_name == "test"
        assert result.plugin_results[0].gib_per_day == 5.0
        assert result.plugin_results[0].confidence == 0.8
    
    def test_confidence_blending(self):
        """Test blending results from multiple plugins based on confidence."""
        # Create plugins with different confidences
        plugin1 = TestPlugin("high_conf", 0.9, 5.0)
        plugin2 = TestPlugin("medium_conf", 0.7, 3.0)
        plugin3 = TestPlugin("low_conf", 0.4, 10.0)
        
        # Create coordinator with all plugins
        coordinator = CostCoordinator(plugins=[plugin1, plugin2, plugin3])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Verify results - should blend high and medium confidence results
        # Ignoring low confidence since we have better options
        expected_blend = (5.0 * 0.9 + 3.0 * 0.7) / (0.9 + 0.7)
        assert round(result.blended_gib_per_day, 2) == round(expected_blend, 2)
        
        # Highest confidence should be reported
        assert result.confidence == 0.9
        
        # All plugins should be called
        assert plugin1.called
        assert plugin2.called
        assert plugin3.called
        
        # Results should be ordered by confidence
        assert result.plugin_results[0].plugin_name == "high_conf"
        assert result.plugin_results[1].plugin_name == "medium_conf"
        assert result.plugin_results[2].plugin_name == "low_conf"
    
    def test_fallback_to_lower_confidence(self):
        """Test falling back to lower confidence plugins when higher ones fail."""
        # Create plugins with different confidences
        plugin1 = TestPlugin("high_conf", 0.9, 5.0, should_fail=True)
        plugin2 = TestPlugin("medium_conf", 0.7, 3.0)
        plugin3 = TestPlugin("low_conf", 0.4, 10.0)
        
        # Create coordinator with all plugins
        coordinator = CostCoordinator(plugins=[plugin1, plugin2, plugin3])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Verify results - should blend medium and low confidence results
        # since high confidence failed
        expected_blend = (3.0 * 0.7 + 10.0 * 0.4) / (0.7 + 0.4)
        assert round(result.blended_gib_per_day, 2) == round(expected_blend, 2)
        
        # Highest successful confidence should be reported
        assert result.confidence == 0.7
        
        # All plugins should be called
        assert plugin1.called
        assert plugin2.called
        assert plugin3.called
        
        # Failed plugin should be marked as failed
        assert len(result.failed_plugins) == 1
        assert result.failed_plugins[0] == "high_conf"
    
    def test_all_plugins_fail(self):
        """Test behavior when all plugins fail."""
        # Create plugins that all fail
        plugin1 = TestPlugin("plugin1", 0.9, 5.0, should_fail=True, error_msg="Error 1")
        plugin2 = TestPlugin("plugin2", 0.7, 3.0, should_fail=True, error_msg="Error 2")
        
        # Create coordinator with failing plugins
        coordinator = CostCoordinator(plugins=[plugin1, plugin2])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimation should raise an exception
        with pytest.raises(ValueError) as exc_info:
            coordinator.estimate(request)
        
        # Error should contain all plugin error messages
        error_msg = str(exc_info.value)
        assert "All cost plugins failed" in error_msg
        assert "Error 1" in error_msg
        assert "Error 2" in error_msg
        
        # All plugins should have been called
        assert plugin1.called
        assert plugin2.called
    
    def test_empty_plugin_list(self):
        """Test behavior with empty plugin list."""
        # Create coordinator with no plugins
        coordinator = CostCoordinator(plugins=[])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimation should raise an exception
        with pytest.raises(ValueError) as exc_info:
            coordinator.estimate(request)
        
        assert "No cost plugins available" in str(exc_info.value)
    
    def test_zero_confidence_handling(self):
        """Test handling of zero confidence plugins."""
        # Create plugins with zero confidence
        plugin1 = TestPlugin("zero_conf", 0.0, 5.0)
        plugin2 = TestPlugin("normal_conf", 0.7, 3.0)
        
        # Create coordinator with the plugins
        coordinator = CostCoordinator(plugins=[plugin1, plugin2])
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Zero confidence plugin should be ignored in blending
        assert result.blended_gib_per_day == 3.0
        assert result.confidence == 0.7
        
        # But it should still be called and included in results
        assert plugin1.called
        assert len(result.plugin_results) == 2
    
    def test_custom_blend_count(self):
        """Test using a custom blend count."""
        # Create several plugins
        plugin1 = TestPlugin("plugin1", 0.9, 5.0)
        plugin2 = TestPlugin("plugin2", 0.8, 3.0)
        plugin3 = TestPlugin("plugin3", 0.7, 2.0)
        plugin4 = TestPlugin("plugin4", 0.6, 1.0)
        
        # Create coordinator with custom blend count
        coordinator = CostCoordinator(plugins=[plugin1, plugin2, plugin3, plugin4], blend_count=3)
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Should blend top 3 plugins
        expected_blend = (5.0 * 0.9 + 3.0 * 0.8 + 2.0 * 0.7) / (0.9 + 0.8 + 0.7)
        assert round(result.blended_gib_per_day, 2) == round(expected_blend, 2)
        
        # All plugins should be called
        assert plugin1.called
        assert plugin2.called
        assert plugin3.called
        assert plugin4.called
    
    def test_event_publishing(self):
        """Test that events are published during estimation."""
        # Create a simple plugin
        plugin = TestPlugin("test", 0.8, 5.0)
        
        # Create a request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Create coordinator with the plugin
        with patch("zcp_cost.coordinator.publish") as mock_publish:
            coordinator = CostCoordinator(plugins=[plugin])
            result = coordinator.estimate(request)
            
            # Verify events were published
            assert mock_publish.call_count == 2
            
            # Check event topics
            call_args_list = mock_publish.call_args_list
            assert call_args_list[0][0][0].topic == "cost.started"
            assert call_args_list[1][0][0].topic == "cost.estimated"
            
            # Check content of estimated event
            estimated_event = call_args_list[1][0][0]
            assert estimated_event.payload["preset_id"] == "test_preset"
            assert estimated_event.payload["host_count"] == 10
            assert estimated_event.payload["gib_per_day"] == 5.0
            assert estimated_event.payload["confidence"] == 0.8
    
    def test_large_host_count(self):
        """Test estimation with a very large host count."""
        # Create a simple plugin
        plugin = TestPlugin("test", 0.8, 0.5)  # 0.5 GiB per day per host
        
        # Create coordinator with the plugin
        coordinator = CostCoordinator(plugins=[plugin])
        
        # Create a request with large host count
        request = CostRequest(
            preset_id="test_preset",
            host_count=10000,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = coordinator.estimate(request)
        
        # Verify results scale correctly with host count
        # Total should be per-host value * host count
        assert result.blended_gib_per_day == 0.5 * 10000
        assert result.total_gib_per_day == 0.5 * 10000
