"""
Linting data models.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class LintSeverity(str, Enum):
    """Severity levels for lint findings."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LintRule(BaseModel):
    """
    Rule definition for linting.
    """
    id: str
    name: str
    description: str
    severity: LintSeverity = LintSeverity.WARNING
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class LintFinding(BaseModel):
    """
    Finding from a lint check.
    """
    rule_id: str
    message: str
    severity: LintSeverity
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    
    class Config:
        extra = "forbid"


class LintRequest(BaseModel):
    """
    Request for linting.
    """
    content: str
    filename: Optional[str] = None
    rules: Optional[List[str]] = None  # List of rule IDs to apply, None means all
    
    class Config:
        extra = "forbid"


class LintResult(BaseModel):
    """
    Result of linting.
    """
    findings: List[LintFinding] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self._update_counts()
    
    def _update_counts(self):
        """Update counts based on findings."""
        self.error_count = sum(1 for f in self.findings if f.severity == LintSeverity.ERROR)
        self.warning_count = sum(1 for f in self.findings if f.severity == LintSeverity.WARNING)
        self.info_count = sum(1 for f in self.findings if f.severity == LintSeverity.INFO)
    
    def add_finding(self, finding: LintFinding):
        """
        Add a finding and update counts.
        
        Args:
            finding: Finding to add
        """
        self.findings.append(finding)
        self._update_counts()
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return self.error_count > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return self.warning_count > 0
    
    @property
    def has_findings(self) -> bool:
        """Check if there are any findings."""
        return len(self.findings) > 0
