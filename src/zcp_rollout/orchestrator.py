"""
Rollout orchestration implementation.
"""

import concurrent.futures
import time
from typing import Dict, List, Optional, Tuple, Type

from zcp_core.bus import Event, publish
from zcp_rollout.backends import AnsibleBackend, BaseBackend, PrintBackend, SSHBackend
from zcp_rollout.models import HostResult, RolloutHost, RolloutJob, RolloutReport


class RolloutOrchestrator:
    """
    Orchestrates configuration rollout to multiple hosts.
    
    Handles parallel execution, backend selection, and reporting.
    """
    
    def __init__(self, backend: Optional[BaseBackend] = None):
        """
        Initialize rollout orchestrator.
        
        Args:
            backend: Rollout backend to use (default: determined by mode)
        """
        self._backend = backend
    
    def _get_backend(self, mode: str) -> BaseBackend:
        """
        Get the appropriate backend based on mode.
        
        Args:
            mode: Backend mode (ssh, ansible, print)
            
        Returns:
            Backend instance
            
        Raises:
            ValueError: If mode is unknown
        """
        if self._backend:
            return self._backend
        
        if mode == "ssh":
            return SSHBackend()
        elif mode == "ansible":
            return AnsibleBackend()
        elif mode == "print":
            return PrintBackend()
        else:
            raise ValueError(f"Unknown backend mode: {mode}")
    
    def _process_host(self, host: RolloutHost, content: str, filename: str, backend: BaseBackend) -> HostResult:
        """
        Process a single host.
        
        Args:
            host: Target host
            content: Configuration content
            filename: Target filename
            backend: Rollout backend
            
        Returns:
            Host result
        """
        # Transfer configuration
        transfer_result = backend.transfer(host, content, filename)
        if not transfer_result.success:
            return transfer_result
        
        # Restart agent
        restart_result = backend.restart(host)
        
        # Use restart result as the final result
        return restart_result
    
    def execute(self, job: RolloutJob, mode: str = "print") -> RolloutReport:
        """
        Execute a rollout job.
        
        Args:
            job: Rollout job
            mode: Backend mode (ssh, ansible, print)
            
        Returns:
            Rollout report
        """
        start_time = time.time()
        backend = self._get_backend(mode)
        results: Dict[str, HostResult] = {}
        
        # Process hosts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=job.parallel) as executor:
            future_to_host = {
                executor.submit(
                    self._process_host, host, job.config_content, job.config_filename, backend
                ): host for host in job.hosts
            }
            
            for future in concurrent.futures.as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    results[host.hostname] = result
                except Exception as e:
                    # Handle exceptions from threads
                    results[host.hostname] = HostResult(
                        hostname=host.hostname,
                        success=False,
                        message=f"Error: {str(e)}"
                    )
        
        # Calculate statistics
        success_count = sum(1 for r in results.values() if r.success)
        fail_count = len(results) - success_count
        duration_s = time.time() - start_time
        
        # Create report
        report = RolloutReport(
            success=success_count,
            fail=fail_count,
            duration_s=duration_s,
            results=results
        )
        
        # Publish event
        publish(Event(
            topic="rollout.completed",
            payload={
                "success": success_count,
                "fail": fail_count,
                "duration_s": duration_s
            }
        ))
        
        return report
