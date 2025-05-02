"""
Simplified rollout implementation.

This module provides a straightforward way to deploy configurations to hosts,
without the complexity of multiple backends or parallel execution.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

@dataclass
class Host:
    """Target host for rollout."""
    hostname: str
    target_path: str = "/etc/newrelic-infra/integrations.d/"

@dataclass
class RolloutResult:
    """Result of a single host rollout."""
    hostname: str
    success: bool
    message: str
    duration_ms: float = 0

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status}: {self.hostname} - {self.message} ({self.duration_ms:.1f}ms)"

@dataclass
class RolloutSummary:
    """Summary of a rollout operation."""
    total: int
    success: int
    failure: int
    duration_ms: float
    results: Dict[str, RolloutResult]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.success / self.total * 100) if self.total > 0 else 0

    def __str__(self):
        return (f"Rollout complete: {self.success}/{self.total} hosts successful "
                f"({self.success_rate:.1f}%) in {self.duration_ms/1000:.2f}s")

def rollout_config(hosts: List[Host], config_content: str, filename: str, 
                   dry_run: bool = True) -> RolloutSummary:
    """
    Roll out a configuration to multiple hosts.
    
    This is a simplified implementation that:
    1. Loops through hosts sequentially (no parallelism)
    2. Uses a single "print" backend that simulates deployment
    3. Returns a basic summary of results
    
    Args:
        hosts: List of target hosts
        config_content: Configuration content to deploy
        filename: Target filename
        dry_run: Whether to actually deploy or just simulate
            
    Returns:
        Summary of rollout results
    """
    start_time = time.time()
    results: Dict[str, RolloutResult] = {}
    
    for host in hosts:
        host_start = time.time()
        target_path = os.path.join(host.target_path, filename)
        
        try:
            # In a real implementation, this would actually transfer the file
            # For dry-run, just log what would happen
            logger.info(f"Would transfer {len(config_content)} bytes to {host.hostname}:{target_path}")
            
            if not dry_run:
                # This would be real implementation
                logger.info(f"Actually deploying to {host.hostname} (not implemented)")
                # For now it's just a placeholder - actual SSH implementation would go here
            
            # Simulate restart
            logger.info(f"Would restart agent on {host.hostname}")
            
            duration_ms = (time.time() - host_start) * 1000
            results[host.hostname] = RolloutResult(
                hostname=host.hostname,
                success=True,
                message=f"Configuration {'would be' if dry_run else 'was'} deployed to {target_path}",
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - host_start) * 1000
            results[host.hostname] = RolloutResult(
                hostname=host.hostname,
                success=False,
                message=f"Error: {str(e)}",
                duration_ms=duration_ms
            )
    
    # Calculate summary
    total_duration_ms = (time.time() - start_time) * 1000
    success_count = sum(1 for r in results.values() if r.success)
    fail_count = len(results) - success_count
    
    summary = RolloutSummary(
        total=len(hosts),
        success=success_count,
        failure=fail_count,
        duration_ms=total_duration_ms,
        results=results
    )
    
    logger.info(str(summary))
    return summary
