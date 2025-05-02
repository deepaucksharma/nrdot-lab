"""
Simplified linting implementation for checking configuration files.

This module provides a straightforward linting approach without the complexity
of dynamic rule registration or extensive abstractions.
"""

import logging
import yaml
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LintSeverity(str, Enum):
    """Severity levels for lint findings."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class LintFinding:
    """A single lint finding."""
    
    def __init__(self, message: str, severity: LintSeverity, line: Optional[int] = None, 
                 column: Optional[int] = None):
        self.message = message
        self.severity = severity
        self.line = line
        self.column = column
    
    def __repr__(self):
        loc = f" at line {self.line}" if self.line is not None else ""
        return f"{self.severity.upper()}: {self.message}{loc}"

class LintResult:
    """Result of linting a configuration file."""
    
    def __init__(self):
        self.findings: List[LintFinding] = []
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(f.severity == LintSeverity.ERROR for f in self.findings)
    
    @property
    def error_count(self) -> int:
        """Get the number of errors."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Get the number of warnings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.WARNING)
    
    def add_finding(self, finding: LintFinding):
        """Add a finding to the result."""
        self.findings.append(finding)
    
    def __str__(self):
        return f"Lint result: {self.error_count} errors, {self.warning_count} warnings"

def lint_config(content: str) -> LintResult:
    """
    Lint a configuration file.
    
    This function performs several checks:
    1. YAML syntax validation
    2. Integration name presence
    3. Sample rate reasonableness
    4. Empty match patterns
    5. Valid discovery mode
    
    Args:
        content: YAML content to lint
            
    Returns:
        Lint result with findings
    """
    result = LintResult()
    
    # Parse YAML if possible
    yaml_content = None
    try:
        yaml_content = yaml.safe_load(content)
    except yaml.YAMLError as e:
        # Extract line and column from the error
        line = getattr(e, "problem_mark", None)
        line_num = getattr(line, "line", None)
        col_num = getattr(line, "column", None)
        
        result.add_finding(
            LintFinding(
                message=f"Invalid YAML syntax: {str(e)}",
                severity=LintSeverity.ERROR,
                line=line_num,
                column=col_num,
            )
        )
        return result
    
    # If not a dict or no content, return
    if not yaml_content or not isinstance(yaml_content, dict):
        result.add_finding(
            LintFinding(
                message="Configuration is empty or not a YAML dictionary",
                severity=LintSeverity.ERROR
            )
        )
        return result
    
    # Check integrations
    integrations = yaml_content.get("integrations", [])
    if not integrations or not isinstance(integrations, list):
        result.add_finding(
            LintFinding(
                message="No integrations defined or 'integrations' is not a list",
                severity=LintSeverity.ERROR
            )
        )
        return result
    
    # Check each integration
    valid_modes = {"include", "exclude"}
    
    for i, integration in enumerate(integrations):
        if not isinstance(integration, dict):
            result.add_finding(
                LintFinding(
                    message=f"Integration at index {i} is not a dictionary",
                    severity=LintSeverity.ERROR
                )
            )
            continue
        
        # Check integration name
        name = integration.get("name")
        if not name:
            result.add_finding(
                LintFinding(
                    message=f"Integration at index {i} is missing a name",
                    severity=LintSeverity.ERROR
                )
            )
        
        config = integration.get("config", {})
        if not isinstance(config, dict):
            result.add_finding(
                LintFinding(
                    message=f"Config for integration '{name or i}' is not a dictionary",
                    severity=LintSeverity.ERROR
                )
            )
            continue
        
        # Check sample rate
        interval = config.get("interval")
        if interval is not None:
            try:
                interval_val = int(interval)
                if interval_val < 5:
                    result.add_finding(
                        LintFinding(
                            message=f"Sample rate interval {interval_val}s is too low (< 5s), may cause high resource usage",
                            severity=LintSeverity.WARNING
                        )
                    )
                elif interval_val > 60:
                    result.add_finding(
                        LintFinding(
                            message=f"Sample rate interval {interval_val}s is high (> 60s), may miss short-lived processes",
                            severity=LintSeverity.INFO
                        )
                    )
            except (ValueError, TypeError):
                result.add_finding(
                    LintFinding(
                        message=f"Invalid sample rate interval: {interval}",
                        severity=LintSeverity.WARNING
                    )
                )
        
        discovery = config.get("discovery", {})
        if not isinstance(discovery, dict):
            result.add_finding(
                LintFinding(
                    message=f"Discovery for integration '{name or i}' is not a dictionary",
                    severity=LintSeverity.ERROR
                )
            )
            continue
        
        # Check discovery mode
        mode = discovery.get("mode")
        if mode is None:
            result.add_finding(
                LintFinding(
                    message="Discovery mode not specified, defaulting to 'include'",
                    severity=LintSeverity.INFO
                )
            )
        elif mode not in valid_modes:
            result.add_finding(
                LintFinding(
                    message=f"Invalid discovery mode: {mode}, must be one of: {', '.join(valid_modes)}",
                    severity=LintSeverity.ERROR
                )
            )
        
        # Check match patterns
        match_patterns = discovery.get("match_patterns", [])
        if not match_patterns:
            result.add_finding(
                LintFinding(
                    message="No match patterns specified, this will match nothing",
                    severity=LintSeverity.ERROR
                )
            )
        elif not isinstance(match_patterns, list):
            result.add_finding(
                LintFinding(
                    message="Match patterns must be a list",
                    severity=LintSeverity.ERROR
                )
            )
        else:
            # Check for empty patterns
            for j, pattern in enumerate(match_patterns):
                if not pattern:
                    result.add_finding(
                        LintFinding(
                            message=f"Empty pattern at index {j}",
                            severity=LintSeverity.ERROR
                        )
                    )
    
    # Log summary
    logger.info(f"Linting complete: {result.error_count} errors, {result.warning_count} warnings")
    
    return result
