"""
Linter implementation for checking configuration files.
"""

import yaml
from typing import Dict, List, Optional, Set

from zcp_core.bus import Event, publish
from zcp_core.schema import validate as validate_schema
from zcp_lint.models import LintFinding, LintRequest, LintResult, LintRule
from zcp_lint.rules import LintRuleRegistry


class Linter:
    """
    Lints configuration files for issues.
    """
    
    def __init__(self, rules: Optional[List[LintRule]] = None):
        """
        Initialize linter.
        
        Args:
            rules: Specific rules to use (default: all enabled rules)
        """
        self._rules = rules or LintRuleRegistry.get_enabled_rules()
    
    def lint(self, request: LintRequest) -> LintResult:
        """
        Lint a configuration file.
        
        Args:
            request: Lint request
            
        Returns:
            Lint result
        """
        result = LintResult()
        
        # Parse YAML if possible
        yaml_content = None
        try:
            yaml_content = yaml.safe_load(request.content)
        except yaml.YAMLError:
            # Syntax error will be caught by appropriate rule
            pass
        
        # Filter rules if requested
        rules_to_apply = self._rules
        if request.rules:
            rule_ids = set(request.rules)
            rules_to_apply = [r for r in self._rules if r.id in rule_ids]
        
        # Apply each rule
        for rule in rules_to_apply:
            check_func = LintRuleRegistry.get_check(rule.id)
            if check_func:
                findings = check_func(request.content, yaml_content)
                for finding in findings:
                    result.add_finding(finding)
        
        # Publish event
        publish(Event(
            topic="lint.finished",
            payload={
                "error_count": result.error_count,
                "warn_count": result.warning_count
            }
        ))
        
        # Validate against schema
        try:
            validate_schema(result.dict(), "LintResult")
        except Exception as e:
            print(f"Warning: Schema validation failed: {e}")
        
        return result
    
    @classmethod
    def get_available_rules(cls) -> List[LintRule]:
        """
        Get all available rules.
        
        Returns:
            List of available rules
        """
        return LintRuleRegistry.get_all_rules()
