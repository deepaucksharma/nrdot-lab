# ZCP Configuration-Only Implementation

This document explains the configuration-only implementation of the Zero Config Process (ZCP) toolkit, which focuses solely on configuration generation and cost estimation.

## Minimalist Approach

This implementation is even more streamlined than the previous lean-core version, focusing exclusively on:

1. **Preset-based configuration**: Load predefined presets
2. **Template Rendering**: Generate configurations from templates
3. **Cost Estimation**: Predict data ingest costs

The following components have been removed:
- ~~**Linting**: No configuration quality checks~~
- ~~**Rollout Management**: No deployment to hosts~~
- ~~**Validation**: No configuration verification~~

## Core Benefits

1. **Extreme simplicity**: The entire implementation fits in one file
2. **Minimal dependencies**: Only requires preset loading functionality
3. **Clear focus**: Does one job well - generate configurations and estimate costs
4. **Faster execution**: No time spent on validation or deployment

## Using the Configuration-Only Version

### Running the Wizard

```bash
python zcp_config_only.py wizard --preset java_heavy --host-count 10
```

This command:
1. Loads the specified preset
2. Generates a configuration based on it
3. Estimates the data ingest cost
4. Displays or saves the resulting configuration

### Individual Commands

You can also run each step separately:

```bash
# List available presets
python zcp_config_only.py preset list

# Show details of a preset
python zcp_config_only.py preset show java_heavy

# Generate a configuration
python zcp_config_only.py generate --preset java_heavy --output config.yaml

# Estimate cost
python zcp_config_only.py estimate --preset java_heavy --host-count 10
```

## Technical Design

The implementation consists of a single file (`config_only_cli.py`) that provides:

1. A `preset` command group for managing presets
2. A `generate` command for creating configurations
3. An `estimate` command for calculating costs
4. A `wizard` command that combines all steps

The cost estimation uses a simple formula:
```
bytes_per_day = host_count * avg_bytes_per_sample * (86400 / sample_rate) * expected_keep_ratio
gib_per_day = bytes_per_day / (1024 * 1024 * 1024)
```

The template rendering uses simple string formatting rather than a template engine.

## When to Use This Version

The configuration-only version is ideal for:

1. **Development and testing**: Generate test configurations quickly
2. **Cost planning**: Estimate ingest before deployment
3. **CI/CD pipelines**: Generate configurations programmatically
4. **Learning**: Understand the core concepts without complexity

If you need deployment capabilities (rollout) or configuration validation, use the full or lean-core versions instead.

## Dependency Graph

The configuration-only version has a minimal dependency graph:

```
config_only_cli.py
  └── zcp_preset.loader
      └── PresetLoader
```

This focused approach makes the code easier to understand, maintain, and extend.
