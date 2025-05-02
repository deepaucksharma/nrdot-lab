# ProcessSample Optimization Lab

A containerized environment that reduces New Relic ProcessSample ingest by 70% without sacrificing observability.

## Core Strategies

| Strategy | Approach | Reduction |
|----------|----------|-----------|
| **Sample Rate** | 60s interval (vs 20s default) | ~67% |
| **Process Filtering** | Exclude non-essential processes | ~5-10% |
| **OpenTelemetry** | System metrics at 10s intervals | Preserves visibility |

## Quick Start

```bash
# Configure credentials
cp .env.example .env
# Edit with your NR license key, API key, and account ID

# Generate configurations
make generate-configs

# Start the lab with optimized settings
make up

# Validate results (after 5-10 minutes)
make validate
```

## Windows Quick Start

```powershell
# Configure credentials
Copy-Item .env.example .env
# Edit with your NR license key, API key, and account ID

# Generate configurations
.\process-lab.ps1 generate-configs

# Start the lab with optimized settings
.\process-lab.ps1 up

# Validate results (after 5-10 minutes)
.\process-lab.ps1 validate
```

## Configuration Options

| Configuration | Command | Use Case |
|----------|---------|----------|
| **Standard** | `make up` | General optimization |
| **Docker-Stats** | `make docker-stats` | Container metrics |
| **Minimal Mounts** | `make minimal` | Restricted filesystem access |
| **Secure Mode** | `make secure-mode` | Toggle secure execution |

## Filter Types

| Filter | Command | Description |
|--------|---------|-------------|
| None | `make filter-none` | No filtering (baseline) |
| Standard | `make filter-standard` | Basic system process filtering |
| Aggressive | `make filter-aggressive` | Maximum filtering (recommended) |
| Targeted | `make filter-targeted` | Whitelist approach - only include specified processes |

## Documentation Map

- [Optimization Concepts](concepts.md)
- [Infrastructure vs OpenTelemetry Comparison](comparison-table.md)
- [Current Scenarios](scenarios.md)
- [Advanced Scenarios](advanced-scenarios.md)
- **How-to Guides**
  - [Installation](how-to/install.md)
  - [Validation](how-to/validate.md)
  - [Troubleshooting](how-to/troubleshoot.md)
  - [Customization](how-to/extend.md)
  - [Windows](how-to/windows.md)
- **Reference**
  - [Technical Architecture](reference/technical-architecture.md)
  - [Infrastructure Configuration](reference/newrelic-infra.md)
  - [OpenTelemetry Configuration](reference/otel-config.md)
  - [NRQL Queries](reference/nrql-cheatsheet.md)

## Key Components

- **Infrastructure Agent**: Collects ProcessSample with optimized configuration
- **OpenTelemetry Collector**: Provides system metrics via hostmetrics receiver
- **Synthetic Load Generator**: Creates realistic process patterns for testing
- **Unified Configuration**: Template-based configuration system for customization

## Prerequisites

- Docker and Docker Compose
- Python 3.6+ (for visualization)
- New Relic account with license key, API key, and account ID