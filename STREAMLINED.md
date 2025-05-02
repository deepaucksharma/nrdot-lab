# ZCP Streamlined Implementation

This document explains the streamlined implementation of the Zero Config Process (ZCP) toolkit. The streamlined version provides the same core functionality with significantly reduced complexity.

## Simplification Goals

1. **Preserve the main workflow**: preset → template → lint → cost → rollout → validate
2. **Remove unnecessary complexity**: event bus backends, multi-plugin cost estimation, multiple backends, etc.
3. **Simplify abstractions**: flatter architecture, fewer layers of indirection
4. **Reduce dependencies**: minimal external libraries required

## Core Components

### 1. Event Bus (bus_simple.py)

The original event bus had three backends (sync memory, async queue, and file trace) with complex concurrency handling. The streamlined version:

- Uses a single synchronous implementation
- Eliminates async/await complexity
- Removes environment-variable switching
- Simplifies subscriber matching

### 2. Cost Estimation (simple_cost.py)

Original cost estimation used multiple weighted plugins with confidence blending. The simplified version:

- Uses a single direct calculation
- Eliminates plugin architecture and confidence weighting
- Keeps the basic formula: `host_count * (avg_bytes / sample_rate) * 86400 / (1024^3)`
- Provides clear, straightforward results

### 3. Linting (simple_lint.py)

Original linting used a complex registry of dynamically registered rules. The streamlined version:

- Combines all rules into a single function
- Removes decorator-based registration
- Maintains the same rule checks (YAML syntax, integration name, sample rate, etc.)
- Uses simpler data structures

### 4. Rollout (simple_rollout.py)

Original rollout had multiple backend implementations and concurrency. The streamlined version:

- Uses a single "print/dry-run" backend (real implementation can be added as needed)
- Processes hosts sequentially for simplicity and debugging
- Provides the same summary information

### 5. Validation (simple_validate.py)

Original validation had circuit breakers and complex error handling. The streamlined version:

- Uses a direct approach to query data
- Simplifies threshold comparison
- Provides cleaner reporting
- Includes a dummy mode for testing without API access

### 6. CLI (simple_cli.py)

Original CLI had many subcommands and complex option handling. The streamlined version:

- Focuses on the core commands: wizard, lint, rollout, validate
- Simplifies options to the essential parameters
- Provides better workflow guidance

## Using the Streamlined Version

### Running the Wizard

```bash
python -m zcp_cli.simple_cli wizard --preset java_heavy --host-count 10
```

This single command takes you through the entire workflow:
1. Loads the preset
2. Renders a configuration
3. Lints it for issues
4. Estimates data ingest cost
5. Optionally deploys it (with `--rollout`)
6. Optionally validates it (with `--validate`)

### Individual Commands

You can also run each step separately:

```bash
# Lint a configuration file
python -m zcp_cli.simple_cli lint config.yaml

# Roll out a configuration
python -m zcp_cli.simple_cli rollout --hosts host1.example.com,host2.example.com --config config.yaml

# Validate the rollout
python -m zcp_cli.simple_cli validate --hosts host1.example.com,host2.example.com --expected 5.4
```

## Benefits of the Streamlined Approach

1. **Easier to understand**: New developers can grasp the entire codebase quickly
2. **Easier to maintain**: Fewer abstractions and simpler code paths
3. **More reliable**: Less complexity means fewer edge cases and bugs
4. **Better performance**: Less overhead from abstraction layers
5. **Smaller footprint**: Fewer dependencies and less code

## Next Steps

If more advanced features are needed, they can be added incrementally:

1. **Real SSH implementation**: Add actual SSH functionality to the rollout module
2. **API integration**: Add real New Relic API integration to the validation module
3. **Additional linting rules**: Add more sophisticated rule checks as needed
4. **More preset types**: Support additional preset configurations

This streamlined implementation focuses on the 80% use case while making it easy to extend for specific needs.
