"""
Unit tests for the linter module.
"""

from unittest.mock import MagicMock, patch

import pytest

from zcp_lint.linter import Linter
from zcp_lint.models import LintRequest, LintResult, LintRule, LintSeverity


class TestLinter:
    """
    Tests for the Linter class.
    """
    
    def test_lint_valid_yaml(self):
        """Test linting valid YAML."""
        # Valid process configuration
        yaml_content = """
        integrations:
          - name: nri-process-discovery
            config:
              interval: 15
              discovery:
                mode: include
                match_patterns:
                  - java
                  - python
        """
        
        # Create request
        request = LintRequest(content=yaml_content, filename="test.yaml")
        
        # Create linter and lint
        with patch("zcp_lint.linter.publish") as mock_publish:
            linter = Linter()
            result = linter.lint(request)
            
            # Should have no errors
            assert result.error_count == 0
            assert not result.has_errors
            
            # Should publish event
            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            assert event.topic == "lint.finished"
            assert event.payload["error_count"] == 0
    
    def test_lint_invalid_yaml(self):
        """Test linting invalid YAML."""
        # Invalid YAML syntax
        yaml_content = """
        integrations:
          - name: nri-process-discovery
            config:
              interval: 15
              discovery:
                mode: include
                match_patterns:
                  - java
                  - python
                  - 
          - name: this is not valid:
            :wut:
        """
        
        # Create request
        request = LintRequest(content=yaml_content, filename="test.yaml")
        
        # Create linter and lint
        with patch("zcp_lint.linter.publish") as mock_publish:
            linter = Linter()
            result = linter.lint(request)
            
            # Should have syntax error
            assert result.error_count > 0
            assert result.has_errors
            
            # Find syntax error finding
            syntax_errors = [f for f in result.findings if f.rule_id == "yaml-syntax"]
            assert len(syntax_errors) > 0
    
    def test_rule_filtering(self):
        """Test filtering rules."""
        # YAML that would trigger multiple rules
        yaml_content = """
        integrations:
          - name: nri-process-discovery
            config:
              interval: 2
              discovery:
                mode: invalid-mode
                match_patterns:
                  - java
                  - ""
        """
        
        # Create request with only certain rules
        request = LintRequest(
            content=yaml_content, 
            filename="test.yaml",
            rules=["sample-rate"]  # Only check sample rate
        )
        
        # Create linter and lint
        linter = Linter()
        result = linter.lint(request)
        
        # Should only have sample-rate findings, not discovery-mode or empty-patterns
        assert all(f.rule_id == "sample-rate" for f in result.findings)
        
        # Should have warning about low sample rate
        sample_rate_warnings = [f for f in result.findings if f.rule_id == "sample-rate"]
        assert len(sample_rate_warnings) > 0
        assert "too low" in sample_rate_warnings[0].message
    
    def test_get_available_rules(self):
        """Test getting available rules."""
        rules = Linter.get_available_rules()
        
        # Should have our standard rules
        rule_ids = {r.id for r in rules}
        assert "yaml-syntax" in rule_ids
        assert "integration-name" in rule_ids
        assert "sample-rate" in rule_ids
        assert "empty-patterns" in rule_ids
        assert "discovery-mode" in rule_ids
