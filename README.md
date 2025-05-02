# ZCP - Zero Config Process

ZCP is a toolkit for configuring, deploying, and managing process monitoring agents at scale.

## Features

- **Preset-based configuration**: Leverage tested configuration templates for common use cases.
- **Cost Estimation**: Predict data ingest costs before deployment.
- **Template Rendering**: Generate agent configurations using Jinja2 templates.
- **Rollout Management**: Safely deploy configurations to large fleets of hosts.
- **Validation**: Verify that deployed configurations are working as expected.
- **Linting**: Check configurations for common issues and best practices.
- **Structured Logging**: Consistent logging with context and OpenTelemetry support.

## Streamlined Version

A streamlined version with simplified architecture is available. It provides the same core workflow with:

- Less complexity and better maintainability
- Fewer dependencies and simpler code paths
- Easier to understand for new developers

Try it with:

```bash
python zcp_simple.py wizard --preset java_heavy --host-count 10
```

See [STREAMLINED.md](STREAMLINED.md) for details.

## Architecture

ZCP follows a modular, event-driven architecture:

- **Control Plane**: Core components that handle configuration and management.
- **Data Plane**: Host agents and data collection infrastructure.

Components communicate via an event bus with pluggable backends (sync, async, or trace mode).

## Getting Started

### Installation

```bash
pip install zcp
```

### Quick Start

```bash
# List available presets
zcp preset list

# Show details of a preset
zcp preset show java_heavy

# Run the configuration wizard
zcp wizard --preset java_heavy --host-count 100

# Lint a configuration
zcp lint check config.yaml

# Deploy to hosts
zcp rollout execute --hosts host1.example.com,host2.example.com --config config.yaml

# Validate configuration
zcp validate check --hosts host1.example.com,host2.example.com --expected 10.5
```

## Components

- `zcp_core`: Core utilities and event bus.
- `zcp_preset`: Preset loading and management.
- `zcp_template`: Template rendering with Jinja2.
- `zcp_cost`: Cost estimation with plugin architecture.
- `zcp_rollout`: Deployment with multiple backends (SSH, Ansible, Print).
- `zcp_validate`: Validation with NRDB integration.
- `zcp_lint`: Configuration linting with rule-based architecture.
- `zcp_logging`: Structured logging with OpenTelemetry support.
- `zcp_cli`: Command-line interface for all components.

## Recent Improvements

The latest release includes several important fixes:

- **Fixed Python 3.11+ compatibility**: Event loops now work correctly in all Python versions.
- **Resolved model/schema discrepancies**: Fixed snake_case vs camelCase inconsistencies.
- **Improved error handling**: Better handling of exceptions in the event bus.
- **Enhanced resource loading**: Resources now load correctly in both development and production.
- **Added Pydantic v2 compatibility**: Code now works with both Pydantic v1 and v2.

For a complete list of fixes, see [FIXES.md](FIXES.md).

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/example/zcp.git
cd zcp

# Install development dependencies
pip install hatch

# Run tests
hatch run test
```

### Development Workflow

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

### Project Status

See [CURRENT_STATUS.md](CURRENT_STATUS.md) for current project status and roadmap.

## Documentation

For full documentation, see the `docs/` directory.

- **Architecture Decisions**: See `docs/adr/` for architecture decision records.
- **Runbooks**: See `docs/runbooks/` for operational runbooks.
- **Test Plans**: See `docs/TEST_IMPROVEMENT_PLAN.md` for testing roadmap.
- **Component READMEs**: Each component has its own README with usage examples.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

