# Runbook: Linting Failures

## Detect

The following signals indicate potential linting issues:

- `zcp lint check` command exits with non-zero status
- Linting events (`lint.finished`) with `error_count > 0` in the event bus
- Pull requests failing CI due to linting errors
- Users reporting configuration issues despite successful rollout

## Diagnose

### Check Lint Results

1. Run linter on the problematic configuration:
   ```bash
   zcp lint check path/to/config.yaml
   ```

2. For detailed JSON output that can be parsed programmatically:
   ```bash
   zcp lint check path/to/config.yaml --format json
   ```

3. Review specific rule violations.

### Check Available Rules

1. List available rules to understand what's being checked:
   ```bash
   zcp lint rules
   ```

2. Check specific rules by filtering:
   ```bash
   zcp lint check path/to/config.yaml --rules yaml-syntax,sample-rate
   ```

### Common Lint Issues

1. **YAML Syntax**: Check for indentation issues, missing colons, or invalid characters
2. **Integration Name**: Verify each integration has a valid name
3. **Sample Rate**: Ensure sampling intervals are reasonable (5-60 seconds)
4. **Empty Patterns**: Check for blank or missing process match patterns
5. **Discovery Mode**: Validate the mode is either "include" or "exclude"

## Mitigate

1. **For syntax errors:**
   Fix indentation, colons, and structure according to YAML specification.

2. **For integration name issues:**
   Ensure each integration has a valid name, such as:
   ```yaml
   integrations:
     - name: nri-process-discovery
   ```

3. **For sample rate issues:**
   Adjust interval to between 5-60 seconds:
   ```yaml
   config:
     interval: 15  # Reasonable value
   ```

4. **For empty patterns:**
   Remove empty patterns and ensure valid patterns exist:
   ```yaml
   match_patterns:
     - java
     - python
     # No empty strings or missing values
   ```

5. **For discovery mode:**
   Set mode to either "include" or "exclude":
   ```yaml
   discovery:
     mode: include  # or "exclude"
   ```

6. **If the configuration was generated by ZCP:**
   Check for preset issues or template problems, then regenerate:
   ```bash
   zcp wizard --preset correct_preset --template correct_template
   ```

## Prevent

1. **Pre-commit hooks:**
   Add linting as a pre-commit hook to catch issues before pushing:
   ```bash
   zcp lint check {files} || exit 1
   ```

2. **CI pipeline integration:**
   Add linting step to CI workflow:
   ```yaml
   lint:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v2
       - name: Lint YAML files
         run: zcp lint check path/to/configs/*.yaml
   ```

3. **Custom rule development:**
   For repeated issues, develop custom rules or enhance existing ones.

4. **Documentation:**
   Create template examples and update documentation to show correct configuration patterns.

5. **Improve templates:**
   Ensure template generation produces lint-clean output by adding template testing.
