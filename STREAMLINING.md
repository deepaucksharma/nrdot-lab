# ProcessSample Optimization Lab - Current Architecture

## Configuration System

### Template-Based Configuration
- Unified template system (`config/newrelic-infra-template.yml`) for infrastructure agent
- Centralized filter definitions file (`config/filter-definitions.yml`)
- Configuration generators (`scripts/generate_configs.[sh|ps1]`)
- Multiple filtering strategies (none, standard, aggressive, targeted)

### OpenTelemetry Configuration
- Template-based OpenTelemetry configuration (`config/otel-template.yaml`)
- Multiple interval options (5s, 10s, 20s, 30s)
- Docker stats collection option
- Lightweight configuration option

### Unified Docker Compose
- Single Docker Compose file with environment variable customization
- Conditional service and volume configurations
- Resource limit controls
- Cross-platform compatibility

## Command Interfaces

### Linux/macOS Interface (Makefile)
- Intuitive commands for common operations
- Filter type and sample rate controls
- Validation and visualization options
- Testing scenario automation

### Windows Interface (process-lab.ps1)
- PowerShell command interface matching Makefile functionality
- Platform-specific path and command handling
- Integrated help system
- Full feature parity with Linux/macOS

## Validation & Visualization

### Validation Tools
- Unified validation scripts with multiple output formats
- Data volume and cost metrics
- Process breakdown capabilities
- Cross-platform support

### Visualization
- Data visualization for test results
- Multiple chart types
- Comparison capabilities
- Cost vs. visibility analysis

## Cross-Platform Support

### Platform Detection
- Automatic platform detection
- Command and path adaptation
- Docker Compose command format detection
- Line ending normalization

### Configuration Adaptation
- Environment-specific path formatting
- Shell script compatibility
- Volume mount adaptation
- Error handling for platform differences
