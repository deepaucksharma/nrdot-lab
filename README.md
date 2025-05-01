# New Relic ProcessSample Optimization Lab

[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://deepaucksharma.github.io/infra-lab/)
[![CI Status](https://img.shields.io/github/actions/workflow/status/deepaucksharma/infra-lab/ci.yml?branch=master&label=ci)](https://github.com/deepaucksharma/infra-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability.

## Core Features

- ~70% reduction in ProcessSample ingestion volume
- Multiple security configurations
- System-level metrics via OpenTelemetry
- Cost validation tools

## Optimization Strategies

1. **Sample Rate**: 60s interval (vs 20s default)
2. **Process Filtering**: Exclude non-essential processes
3. **OTel Metrics**: High-frequency system metrics

## Quick Start

```bash
# Configure credentials
cp .env.example .env
# Edit .env with your New Relic license key, API key, and account ID

# Start the lab
make up

# Validate results (after 5 minutes)
make validate
```

## Available Scenarios

| Scenario | Command | Purpose |
|----------|---------|---------|
| Standard | `make up` | Default optimization |
| Minimal-Mounts | `COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up` | Enhanced security |
| Docker-Stats | `COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up` | Container metrics |
| Seccomp-Off | `COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up` | Troubleshooting |

## Requirements

- Docker and Docker Compose
- `jq` for validation
- New Relic account with license key, API key, and account ID

## Documentation

[View the complete documentation](https://deepaucksharma.github.io/infra-lab/)