"""
Preset model definitions.
"""

import hashlib
import json
from typing import ClassVar, List, Optional

import yaml
from pydantic import BaseModel, Field, validator


class Preset(BaseModel):
    """
    Preset configuration for ZCP.
    
    A preset defines configuration defaults for monitoring agent setup,
    including sampling rates, filtering patterns, and expected resource utilization.
    """
    id: str
    default_sample_rate: int
    filter_mode: str
    tier1_patterns: List[str]
    expected_keep_ratio: float
    avg_bytes_per_sample: int
    sha256: Optional[str] = None
    
    # Class-level constants
    FILTER_MODES: ClassVar[List[str]] = ["include", "exclude"]
    
    @validator("filter_mode")
    def validate_filter_mode(cls, v):
        """Validate filter mode is one of the allowed values."""
        if v not in cls.FILTER_MODES:
            raise ValueError(f"filter_mode must be one of {cls.FILTER_MODES}")
        return v
    
    @validator("expected_keep_ratio")
    def validate_keep_ratio(cls, v):
        """Validate keep ratio is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("expected_keep_ratio must be between 0 and 1")
        return v
    
    @classmethod
    def from_yaml(cls, yml: str) -> "Preset":
        """
        Create a Preset from YAML text.
        
        Args:
            yml: YAML text representation of the preset
            
        Returns:
            A new Preset instance
        """
        data = yaml.safe_load(yml)
        
        # Calculate SHA-256 hash of the input YAML
        data["sha256"] = hashlib.sha256(yml.encode()).hexdigest()
        
        return cls(**data)
    
    def to_json(self) -> str:
        """
        Convert the preset to JSON.
        
        Returns:
            JSON string representation of the preset
        """
        return json.dumps(self.dict(), indent=2)
