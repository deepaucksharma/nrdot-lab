"""
Validation data models.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ValidationJob(BaseModel):
    """
    Definition of a validation job.
    """
    hosts: List[str]
    expected_gib_day: float
    confidence: float  # 0-1
    timeframe_hours: int = 24  # Default to 24 hours
    threshold: float = 0.10  # Default to 10% deviation allowed
    
    @validator("confidence")
    def validate_confidence(cls, v):
        """Validate confidence is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return v
    
    @validator("threshold")
    def validate_threshold(cls, v):
        """Validate threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("threshold must be between 0 and 1")
        return v


class HostValidationResult(BaseModel):
    """
    Validation result for a single host.
    """
    hostname: str
    expected_gib_day: float
    actual_gib_day: float
    within_threshold: bool
    deviation_percent: float
    message: str
    
    @property
    def deviation_ratio(self) -> float:
        """
        Calculate the deviation ratio (actual/expected).
        
        Returns:
            Ratio of actual to expected ingest
        """
        if self.expected_gib_day > 0:
            return self.actual_gib_day / self.expected_gib_day
        return float("inf") if self.actual_gib_day > 0 else 1.0


class ValidationResult(BaseModel):
    """
    Overall validation result.
    """
    pass_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)
    host_results: Dict[str, HostValidationResult] = Field(default_factory=dict)
    overall_pass: bool = False
    summary: str = ""
    query_duration_ms: float = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate overall pass status
        if self.host_results:
            # Pass if all hosts are within threshold
            self.overall_pass = all(r.within_threshold for r in self.host_results.values())
            
            # Generate summary
            pass_count = sum(1 for r in self.host_results.values() if r.within_threshold)
            total_count = len(self.host_results)
            self.pass_rate = pass_count / total_count if total_count > 0 else 0.0
            
            self.summary = (
                f"Validation {'PASSED' if self.overall_pass else 'FAILED'}: "
                f"{pass_count}/{total_count} hosts within threshold "
                f"({self.pass_rate:.1%})"
            )
