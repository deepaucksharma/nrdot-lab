# ZCP Linting Module

The linting module validates configuration files for common issues and best practices.

## Features

- **Rule-Based Architecture**: Pluggable rules for different checks
- **Multiple Severity Levels**: ERROR, WARNING, INFO for graduated responses
- **YAML Validation**: Syntax checking and structure validation
- **Best Practice Rules**: Sample rate, discovery mode, pattern validation
- **CLI Integration**: Easy validation through command-line interface
- **Schema Validation**: Ensures consistent result structure

## Usage

### CLI Examples

```bash
# Lint a configuration file
zcp lint check config.yaml

# List available lint rules
zcp lint rules

# Apply only specific rules
zcp lint check config.yaml --rules yaml-syntax,sample-rate
```

### Programmatic Example

```python
from zcp_lint.linter import Linter
from zcp_lint.models import LintRequest

# Create lint request
request = LintRequest(
    content="yaml content here",
    filename="config.yaml",
    rules=["yaml-syntax", "sample-rate"]  # Optional: specific rules
)

# Create linter and check
linter = Linter()
result = linter.lint(request)

# Use lint result
print(f"Errors: {result.error_count}, Warnings: {result.warning_count}")
for finding in result.findings:
    print(f"[{finding.rule_id}] {finding.message}")
```

## Available Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| yaml-syntax | ERROR | Validates YAML syntax |
| integration-name | ERROR | Checks for valid integration names |
| sample-rate | WARNING | Validates sampling intervals |
| empty-patterns | ERROR | Detects empty matching patterns |
| discovery-mode | ERROR | Checks for valid discovery modes |

## Adding New Rules

Rules can be added by registering them with the rule registry:

```python
from zcp_lint.models import LintRule, LintSeverity, LintFinding
from zcp_lint.rules import LintRuleRegistry

# Define a new rule
new_rule = LintRule(
    id="my-custom-rule",
    name="My Custom Rule",
    description="Checks for a custom condition",
    severity=LintSeverity.WARNING
)

# Register the rule with a check function
@LintRuleRegistry.register(new_rule)
def check_my_custom_rule(content: str, yaml_content: Optional[Dict] = None) -> List[LintFinding]:
    # Implement rule check logic
    findings = []
    # ...
    return findings
```

## Schema

Lint results follow the LintResult schema defined in schema/v1/LintResult.schema.json:

```json
{
  "findings": [
    {
      "rule_id": "sample-rate",
      "message": "Sample rate interval 2s is too low (< 5s), may cause high resource usage",
      "severity": "warning",
      "line": 4
    }
  ],
  "error_count": 0,
  "warning_count": 1,
  "info_count": 0
}
```

## Testing

The module includes unit tests for the linter functionality:

```bash
pytest tests/unit/lint/
```

### Sample Files

The `examples/` directory contains sample configurations for testing:
- `process_config_good.yaml` - A valid configuration
- `process_config_bad.yaml` - A configuration with various issues
