"""
Linting rules implementation.
"""

import re
import yaml
from typing import Dict, List, Optional, Protocol, Set, Type

from zcp_lint.models import LintFinding, LintRule, LintSeverity


class RuleCheck(Protocol):
    """Protocol for rule check functions."""
    
    def __call__(self, content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
        """
        Check content against a rule.
        
        Args:
            content: YAML content as string
            yaml_content: Parsed YAML content (if available)
            
        Returns:
            List of findings
        """
        ...


class LintRuleRegistry:
    """
    Registry of available lint rules.
    """
    
    _rules: Dict[str, LintRule] = {}
    _checks: Dict[str, RuleCheck] = {}
    
    @classmethod
    def register(cls, rule: LintRule):
        """
        Decorator to register a rule check function.
        
        Args:
            rule: Rule definition
            
        Returns:
            Decorator function
        """
        def decorator(check_func: RuleCheck) -> RuleCheck:
            cls._rules[rule.id] = rule
            cls._checks[rule.id] = check_func
            return check_func
        return decorator
    
    @classmethod
    def get_rule(cls, rule_id: str) -> Optional[LintRule]:
        """
        Get a rule by ID.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Rule definition or None if not found
        """
        return cls._rules.get(rule_id)
    
    @classmethod
    def get_check(cls, rule_id: str) -> Optional[RuleCheck]:
        """
        Get a check function by rule ID.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Check function or None if not found
        """
        return cls._checks.get(rule_id)
    
    @classmethod
    def get_all_rules(cls) -> List[LintRule]:
        """
        Get all registered rules.
        
        Returns:
            List of all rules
        """
        return list(cls._rules.values())
    
    @classmethod
    def get_enabled_rules(cls) -> List[LintRule]:
        """
        Get all enabled rules.
        
        Returns:
            List of enabled rules
        """
        return [r for r in cls._rules.values() if r.enabled]


# Register rules with their check functions

@LintRuleRegistry.register(
    LintRule(
        id="yaml-syntax",
        name="YAML Syntax",
        description="Check for valid YAML syntax",
        severity=LintSeverity.ERROR,
    )
)
def check_yaml_syntax(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    """
    Check for valid YAML syntax.
    
    Args:
        content: YAML content as string
        yaml_content: Parsed YAML content (if available)
        
    Returns:
        List of findings
    """
    findings = []
    
    try:
        if yaml_content is None:
            yaml.safe_load(content)
    except yaml.YAMLError as e:
        # Extract line and column from the error
        line = getattr(e, "problem_mark", None)
        line_num = getattr(line, "line", None)
        col_num = getattr(line, "column", None)
        
        findings.append(
            LintFinding(
                rule_id="yaml-syntax",
                message=f"Invalid YAML syntax: {str(e)}",
                severity=LintSeverity.ERROR,
                line=line_num,
                column=col_num,
            )
        )
    
    return findings


@LintRuleRegistry.register(
    LintRule(
        id="integration-name",
        name="Integration Name",
        description="Check for valid integration name",
        severity=LintSeverity.ERROR,
    )
)
def check_integration_name(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    """
    Check for valid integration name.
    
    Args:
        content: YAML content as string
        yaml_content: Parsed YAML content (if available)
        
    Returns:
        List of findings
    """
    findings = []
    
    if yaml_content is None:
        try:
            yaml_content = yaml.safe_load(content)
        except yaml.YAMLError:
            # Syntax error will be caught by yaml-syntax rule
            return findings
    
    # Check if this is an integrations config
    if not yaml_content or not isinstance(yaml_content, dict):
        return findings
    
    integrations = yaml_content.get("integrations", [])
    if not integrations or not isinstance(integrations, list):
        return findings
    
    for i, integration in enumerate(integrations):
        if not isinstance(integration, dict):
            continue
        
        name = integration.get("name")
        if not name:
            findings.append(
                LintFinding(
                    rule_id="integration-name",
                    message=f"Integration at index {i} is missing a name",
                    severity=LintSeverity.ERROR,
                )
            )
    
    return findings


@LintRuleRegistry.register(
    LintRule(
        id="sample-rate",
        name="Sample Rate",
        description="Check for reasonable sample rate values",
        severity=LintSeverity.WARNING,
    )
)
def check_sample_rate(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    """
    Check for reasonable sample rate values.
    
    Args:
        content: YAML content as string
        yaml_content: Parsed YAML content (if available)
        
    Returns:
        List of findings
    """
    findings = []
    
    if yaml_content is None:
        try:
            yaml_content = yaml.safe_load(content)
        except yaml.YAMLError:
            # Syntax error will be caught by yaml-syntax rule
            return findings
    
    # Check if this is an integrations config
    if not yaml_content or not isinstance(yaml_content, dict):
        return findings
    
    integrations = yaml_content.get("integrations", [])
    if not integrations or not isinstance(integrations, list):
        return findings
    
    for i, integration in enumerate(integrations):
        if not isinstance(integration, dict):
            continue
        
        config = integration.get("config", {})
        if not isinstance(config, dict):
            continue
        
        interval = config.get("interval")
        if interval is not None:
            try:
                interval_val = int(interval)
                if interval_val < 5:
                    findings.append(
                        LintFinding(
                            rule_id="sample-rate",
                            message=f"Sample rate interval {interval_val}s is too low (< 5s), may cause high resource usage",
                            severity=LintSeverity.WARNING,
                        )
                    )
                elif interval_val > 60:
                    findings.append(
                        LintFinding(
                            rule_id="sample-rate",
                            message=f"Sample rate interval {interval_val}s is high (> 60s), may miss short-lived processes",
                            severity=LintSeverity.INFO,
                        )
                    )
            except (ValueError, TypeError):
                findings.append(
                    LintFinding(
                        rule_id="sample-rate",
                        message=f"Invalid sample rate interval: {interval}",
                        severity=LintSeverity.WARNING,
                    )
                )
    
    return findings


@LintRuleRegistry.register(
    LintRule(
        id="empty-patterns",
        name="Empty Patterns",
        description="Check for empty match patterns",
        severity=LintSeverity.ERROR,
    )
)
def check_empty_patterns(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    """
    Check for empty match patterns.
    
    Args:
        content: YAML content as string
        yaml_content: Parsed YAML content (if available)
        
    Returns:
        List of findings
    """
    findings = []
    
    if yaml_content is None:
        try:
            yaml_content = yaml.safe_load(content)
        except yaml.YAMLError:
            # Syntax error will be caught by yaml-syntax rule
            return findings
    
    # Check if this is an integrations config
    if not yaml_content or not isinstance(yaml_content, dict):
        return findings
    
    integrations = yaml_content.get("integrations", [])
    if not integrations or not isinstance(integrations, list):
        return findings
    
    for i, integration in enumerate(integrations):
        if not isinstance(integration, dict):
            continue
        
        config = integration.get("config", {})
        if not isinstance(config, dict):
            continue
        
        discovery = config.get("discovery", {})
        if not isinstance(discovery, dict):
            continue
        
        match_patterns = discovery.get("match_patterns", [])
        if not match_patterns:
            findings.append(
                LintFinding(
                    rule_id="empty-patterns",
                    message="No match patterns specified, this will match nothing",
                    severity=LintSeverity.ERROR,
                )
            )
            continue
        
        if not isinstance(match_patterns, list):
            findings.append(
                LintFinding(
                    rule_id="empty-patterns",
                    message="Match patterns must be a list",
                    severity=LintSeverity.ERROR,
                )
            )
            continue
        
        # Check for empty patterns
        for j, pattern in enumerate(match_patterns):
            if not pattern:
                findings.append(
                    LintFinding(
                        rule_id="empty-patterns",
                        message=f"Empty pattern at index {j}",
                        severity=LintSeverity.ERROR,
                    )
                )
    
    return findings


@LintRuleRegistry.register(
    LintRule(
        id="discovery-mode",
        name="Discovery Mode",
        description="Check for valid discovery mode",
        severity=LintSeverity.ERROR,
    )
)
def check_discovery_mode(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    """
    Check for valid discovery mode.
    
    Args:
        content: YAML content as string
        yaml_content: Parsed YAML content (if available)
        
    Returns:
        List of findings
    """
    findings = []
    
    if yaml_content is None:
        try:
            yaml_content = yaml.safe_load(content)
        except yaml.YAMLError:
            # Syntax error will be caught by yaml-syntax rule
            return findings
    
    # Check if this is an integrations config
    if not yaml_content or not isinstance(yaml_content, dict):
        return findings
    
    integrations = yaml_content.get("integrations", [])
    if not integrations or not isinstance(integrations, list):
        return findings
    
    valid_modes = {"include", "exclude"}
    
    for i, integration in enumerate(integrations):
        if not isinstance(integration, dict):
            continue
        
        config = integration.get("config", {})
        if not isinstance(config, dict):
            continue
        
        discovery = config.get("discovery", {})
        if not isinstance(discovery, dict):
            continue
        
        mode = discovery.get("mode")
        if mode is None:
            findings.append(
                LintFinding(
                    rule_id="discovery-mode",
                    message="Discovery mode not specified, defaulting to 'include'",
                    severity=LintSeverity.INFO,
                )
            )
        elif mode not in valid_modes:
            findings.append(
                LintFinding(
                    rule_id="discovery-mode",
                    message=f"Invalid discovery mode: {mode}, must be one of: {', '.join(valid_modes)}",
                    severity=LintSeverity.ERROR,
                )
            )
    
    return findings
