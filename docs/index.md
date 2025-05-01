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

# Start the lab
make up

# Check results (after 5 minutes)
make validate
```

## Scenarios

| Scenario | Command | Use Case |
|----------|---------|----------|
| **Standard** | `make up` | General optimization |
| **Docker-Stats** | `make docker-stats` | Container metrics |

## Documentation Map

- [Optimization Concepts](concepts.md)
- [Infrastructure vs OpenTelemetry Comparison](comparison-table.md)
- [Current Scenarios](scenarios.md)
- [Advanced Scenarios](advanced-scenarios.md)
- [Strategic Roadmap](roadmap.md)
- **How-to Guides**
  - [Installation](how-to/install.md)
  - [Validation](how-to/validate.md)
  - [Troubleshooting](how-to/troubleshoot.md)
  - [Customization](how-to/extend.md)
- **Reference**
  - [Technical Architecture](reference/technical-architecture.md)
  - [Infrastructure Configuration](reference/newrelic-infra.md)
  - [OpenTelemetry Configuration](reference/otel-config.md)
  - [NRQL Queries](reference/nrql-cheatsheet.md)

## Key Components

- **Infrastructure Agent**: Collects ProcessSample with optimized configuration
- **OpenTelemetry Collector**: Provides system metrics via hostmetrics receiver
- **Synthetic Load Generator**: Creates realistic process patterns for testing

## Prerequisites

- Docker and Docker Compose
- `jq` (for validation)
- New Relic account with license key, API key, and account ID