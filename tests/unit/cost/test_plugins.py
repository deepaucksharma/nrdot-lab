"""
Unit tests for the cost estimation plugins.

These tests validate:
1. Static plugin behavior
2. Plugin confidence reporting
3. Cost calculation accuracy
4. Parameter handling
"""

from unittest.mock import MagicMock, patch

import pytest

from zcp_cost.plugin import CostPlugin, CostRequest, StaticPlugin


class TestStaticPlugin:
    """Tests for the static cost plugin."""
    
    def test_basic_estimation(self):
        """Test basic cost estimation with default values."""
        # Create a plugin with default values
        plugin = StaticPlugin()
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = plugin.estimate(request)
        
        # Verify default values
        assert result["gib_per_day"] == 1.0  # Default value
        assert result["confidence"] == 0.5  # Default confidence
    
    def test_custom_values(self):
        """Test cost estimation with custom values."""
        # Create a plugin with custom values
        plugin = StaticPlugin(name="custom", confidence=0.8, gib_per_day=5.0)
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = plugin.estimate(request)
        
        # Verify custom values
        assert result["gib_per_day"] == 5.0
        assert result["confidence"] == 0.8
        assert plugin.name == "custom"
    
    def test_host_count_scaling(self):
        """Test that results scale with host count."""
        # Create a plugin
        plugin = StaticPlugin(gib_per_day=2.0)
        
        # Test with different host counts
        host_counts = [1, 10, 100, 1000]
        
        for count in host_counts:
            # Create request with specific host count
            request = CostRequest(
                preset_id="test_preset",
                host_count=count,
                sample_rate=15,
                filter_patterns=["java", "python"],
                filter_mode="include"
            )
            
            # Estimate cost
            result = plugin.estimate(request)
            
            # Verify per-host value is used
            assert result["gib_per_day"] == 2.0
            
            # Total should be per-host * count
            assert result["total_gib_per_day"] == 2.0 * count
    
    def test_sample_rate_effect(self):
        """Test that sample rate affects the estimate."""
        # Create a plugin that uses sample rate
        class SampleRatePlugin(StaticPlugin):
            def estimate(self, request):
                result = super().estimate(request)
                # Adjust based on sample rate (higher rate = more data)
                result["gib_per_day"] = result["gib_per_day"] * (request.sample_rate / 15)
                result["total_gib_per_day"] = result["gib_per_day"] * request.host_count
                return result
        
        plugin = SampleRatePlugin(gib_per_day=1.0)
        
        # Test with different sample rates
        sample_rates = [5, 15, 30]
        
        for rate in sample_rates:
            # Create request with specific sample rate
            request = CostRequest(
                preset_id="test_preset",
                host_count=10,
                sample_rate=rate,
                filter_patterns=["java", "python"],
                filter_mode="include"
            )
            
            # Estimate cost
            result = plugin.estimate(request)
            
            # Verify sample rate effect
            expected = 1.0 * (rate / 15)
            assert result["gib_per_day"] == expected
            assert result["total_gib_per_day"] == expected * 10
    
    def test_filter_pattern_effect(self):
        """Test that filter patterns affect the estimate."""
        # Create a plugin that uses filter patterns
        class PatternCountPlugin(StaticPlugin):
            def estimate(self, request):
                result = super().estimate(request)
                # Adjust based on pattern count
                pattern_factor = len(request.filter_patterns) / 3  # Normalize to 3 patterns
                result["gib_per_day"] = result["gib_per_day"] * pattern_factor
                result["total_gib_per_day"] = result["gib_per_day"] * request.host_count
                return result
        
        plugin = PatternCountPlugin(gib_per_day=1.5)
        
        # Test with different pattern counts
        pattern_sets = [
            ["java"],
            ["java", "python", "nodejs"],
            ["java", "python", "nodejs", "php", "ruby", "dotnet"]
        ]
        
        for patterns in pattern_sets:
            # Create request with specific patterns
            request = CostRequest(
                preset_id="test_preset",
                host_count=10,
                sample_rate=15,
                filter_patterns=patterns,
                filter_mode="include"
            )
            
            # Estimate cost
            result = plugin.estimate(request)
            
            # Verify pattern count effect
            expected = 1.5 * (len(patterns) / 3)
            assert result["gib_per_day"] == expected
            assert result["total_gib_per_day"] == expected * 10
    
    def test_filter_mode_effect(self):
        """Test that filter mode affects the estimate."""
        # Create a plugin that uses filter mode
        class FilterModePlugin(StaticPlugin):
            def estimate(self, request):
                result = super().estimate(request)
                # Adjust based on filter mode
                if request.filter_mode == "include":
                    # Include mode is more precise, less data
                    result["gib_per_day"] = result["gib_per_day"] * 0.7
                else:
                    # Exclude mode captures more data
                    result["gib_per_day"] = result["gib_per_day"] * 1.3
                result["total_gib_per_day"] = result["gib_per_day"] * request.host_count
                return result
        
        plugin = FilterModePlugin(gib_per_day=1.0)
        
        # Test with different filter modes
        filter_modes = ["include", "exclude"]
        
        for mode in filter_modes:
            # Create request with specific filter mode
            request = CostRequest(
                preset_id="test_preset",
                host_count=10,
                sample_rate=15,
                filter_patterns=["java", "python"],
                filter_mode=mode
            )
            
            # Estimate cost
            result = plugin.estimate(request)
            
            # Verify filter mode effect
            if mode == "include":
                expected = 1.0 * 0.7
            else:
                expected = 1.0 * 1.3
            assert result["gib_per_day"] == expected
            assert result["total_gib_per_day"] == expected * 10
    
    def test_plugin_base_class(self):
        """Test the base plugin class interface."""
        # Create a minimal implementation
        class MinimalPlugin(CostPlugin):
            @property
            def name(self):
                return "minimal"
            
            @property
            def confidence(self):
                return 0.5
            
            def estimate(self, request):
                return {
                    "gib_per_day": 1.0,
                    "confidence": self.confidence
                }
        
        # Create an instance and test
        plugin = MinimalPlugin()
        
        # Create a basic request
        request = CostRequest(
            preset_id="test_preset",
            host_count=10,
            sample_rate=15,
            filter_patterns=["java", "python"],
            filter_mode="include"
        )
        
        # Estimate cost
        result = plugin.estimate(request)
        
        # Verify results
        assert plugin.name == "minimal"
        assert plugin.confidence == 0.5
        assert result["gib_per_day"] == 1.0
        assert result["confidence"] == 0.5
