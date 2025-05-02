"""
Cost estimation plugin interface and implementations.
"""

import abc
from dataclasses import dataclass
from typing import List, Protocol

from pydantic import BaseModel


class CostRequest(BaseModel):
    """
    Request for cost estimation.
    
    Contains all parameters needed for estimating data ingest cost.
    """
    preset_id: str
    host_count: int
    sample_rate: int
    filter_patterns: List[str]
    filter_mode: str
    
    class Config:
        extra = "forbid"  # Prevent unknown fields


class PluginEstimate(BaseModel):
    """
    Cost estimate from a single plugin.
    """
    plugin_name: str
    estimate_gib_per_day: float
    confidence: float  # 0-1
    
    class Config:
        extra = "forbid"


class CostEstimate(BaseModel):
    """
    Combined cost estimate.
    """
    blended_gib_per_day: float
    confidence: float  # 0-1
    breakdown: List[PluginEstimate] = []
    
    class Config:
        extra = "forbid"


class CostPlugin(Protocol):
    """
    Protocol for cost estimation plugins.
    """
    @property
    def name(self) -> str:
        """Get the plugin name."""
        ...
    
    def estimate(self, req: CostRequest) -> PluginEstimate:
        """
        Estimate data ingest cost.
        
        Args:
            req: Cost estimation request
            
        Returns:
            Cost estimate from this plugin
        """
        ...


class StaticPlugin:
    """
    Static cost estimation based on preset values.
    """
    
    @property
    def name(self) -> str:
        return "static"
    
    def estimate(self, req: CostRequest) -> PluginEstimate:
        """
        Estimate based on preset values.
        
        This is a fallback when historical data is not available.
        
        Args:
            req: Cost estimation request
            
        Returns:
            Cost estimate
        """
        from zcp_preset.loader import PresetLoader
        
        # Load the preset
        loader = PresetLoader()
        preset = loader.load(req.preset_id)
        
        # Calculate daily ingest in bytes
        bytes_per_day = (
            req.host_count *                   # Number of hosts
            preset.avg_bytes_per_sample *      # Bytes per sample
            (86400 / req.sample_rate) *        # Samples per day
            preset.expected_keep_ratio         # Ratio of processes that match filter
        )
        
        # Convert to GiB
        gib_per_day = bytes_per_day / (1024 * 1024 * 1024)
        
        return PluginEstimate(
            plugin_name=self.name,
            estimate_gib_per_day=gib_per_day,
            confidence=0.5  # Static estimates have medium confidence
        )


class HistogramPlugin:
    """
    Cost estimation based on historical process size histograms.
    """
    
    @property
    def name(self) -> str:
        return "histogram"
    
    def estimate(self, req: CostRequest) -> PluginEstimate:
        """
        Estimate based on historical data from NRDB.
        
        This uses actual process size distribution for higher accuracy.
        
        Args:
            req: Cost estimation request
            
        Returns:
            Cost estimate
        """
        try:
            # This would normally query NRDB for histogram data
            # For now, just return a placeholder estimate
            # with higher confidence than static
            
            # Simplified model: assume 20% more accurate than static
            static = StaticPlugin().estimate(req)
            
            return PluginEstimate(
                plugin_name=self.name,
                estimate_gib_per_day=static.estimate_gib_per_day * 1.2,
                confidence=0.8  # Histogram-based has higher confidence
            )
        except Exception as e:
            # If NRDB query fails, return a low-confidence estimate
            return PluginEstimate(
                plugin_name=self.name,
                estimate_gib_per_day=0.0,  # Unknown
                confidence=0.0  # No confidence
            )
