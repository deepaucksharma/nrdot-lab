"""
Cost coordinator implementation.
"""

from typing import List

from zcp_core.bus import Event, publish
from zcp_core.schema import validate
from zcp_cost.plugin import CostEstimate, CostPlugin, CostRequest, PluginEstimate


class CostCoordinator:
    """
    Coordinates multiple cost plugins and produces a blended estimate.
    """
    
    def __init__(self, plugins: List[CostPlugin] = None, blend_count: int = 2):
        """
        Initialize the cost coordinator.
        
        Args:
            plugins: List of cost plugins to use
            blend_count: Number of highest-confidence estimates to blend
        """
        self._plugins = plugins or []
        self._blend_count = blend_count
    
    def estimate(self, req: CostRequest) -> CostEstimate:
        """
        Estimate data ingest cost using all available plugins.
        
        Args:
            req: Cost estimation request
            
        Returns:
            Blended cost estimate
        """
        # Get estimates from all plugins
        estimates: List[PluginEstimate] = []
        for plugin in self._plugins:
            try:
                plugin_estimate = plugin.estimate(req)
                estimates.append(plugin_estimate)
            except Exception as e:
                # Log error but continue with other plugins
                print(f"Error in plugin {plugin.name}: {e}")
        
        # Sort by confidence (descending)
        estimates.sort(key=lambda e: e.confidence, reverse=True)
        
        # Blend the top N estimates, weighted by confidence
        top_estimates = estimates[:self._blend_count]
        if not top_estimates:
            # No estimates available
            return CostEstimate(
                blended_gib_per_day=0.0,
                confidence=0.0,
                breakdown=[]
            )
        
        # Calculate weighted average
        total_weight = sum(e.confidence for e in top_estimates)
        if total_weight > 0:
            blended_gib = sum(
                e.estimate_gib_per_day * e.confidence for e in top_estimates
            ) / total_weight
            # Overall confidence is average of top estimates
            overall_confidence = sum(e.confidence for e in top_estimates) / len(top_estimates)
        else:
            # No confidence, use simple average
            blended_gib = sum(e.estimate_gib_per_day for e in top_estimates) / len(top_estimates)
            overall_confidence = 0.0
        
        # Create and validate result
        result = CostEstimate(
            blended_gib_per_day=blended_gib,
            confidence=overall_confidence,
            breakdown=estimates
        )
        
        # Validate against schema (dict() method now uses by_alias=True by default)
        validate(result.dict(), "CostEstimate")
        
        # Publish event
        publish(Event(
            topic="cost.estimated",
            payload={
                "blended_gib_day": result.blended_gib_per_day,
                "confidence": result.confidence
            }
        ))
        
        return result
