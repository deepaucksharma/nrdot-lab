"""
Rollout data models.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RolloutHost(BaseModel):
    """
    Host configuration for rollout.
    """
    hostname: str
    ssh_user: Optional[str] = None
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    use_sudo: bool = False
    target_path: str = "/etc/newrelic-infra/integrations.d/"


class RolloutJob(BaseModel):
    """
    Definition of a rollout job.
    """
    hosts: List[RolloutHost]
    config_content: str
    config_filename: str
    checksum: str
    parallel: int = 10
    timeout_s: int = 30
    
    @classmethod
    def from_host_list(cls, hosts: List[str], config_content: str, filename: str, checksum: str) -> "RolloutJob":
        """
        Create a rollout job from a simple list of hostnames.
        
        Args:
            hosts: List of hostnames
            config_content: Configuration content to deploy
            filename: Target filename
            checksum: Configuration checksum
            
        Returns:
            RolloutJob instance
        """
        return cls(
            hosts=[RolloutHost(hostname=h) for h in hosts],
            config_content=config_content,
            config_filename=filename,
            checksum=checksum
        )


class HostResult(BaseModel):
    """
    Result of rollout to a single host.
    """
    hostname: str
    success: bool
    message: str
    duration_ms: float = 0


class RolloutReport(BaseModel):
    """
    Report on a completed rollout.
    """
    success: int
    fail: int
    duration_s: float
    results: Dict[str, HostResult] = Field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """
        Calculate the success rate.
        
        Returns:
            Success rate as a fraction (0-1)
        """
        total = self.success + self.fail
        return self.success / total if total > 0 else 0.0
