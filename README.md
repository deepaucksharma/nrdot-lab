# New Relic ProcessSample Optimization Lab

[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://deepaucksharma.github.io/infra-lab/)
[![CI Status](https://img.shields.io/github/actions/workflow/status/deepaucksharma/infra-lab/ci.yml?branch=master&label=ci)](https://github.com/deepaucksharma/infra-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability.

## Core Features

- ~70% reduction in ProcessSample ingestion volume
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
| Default | `make up` | Default optimization |
| Docker Stats | `make docker-stats` | Add container metrics |

## Requirements

- Docker and Docker Compose v2
- `jq` for validation
- New Relic account with license key, API key, and account ID

## Documentation

[View the complete documentation](https://deepaucksharma.github.io/infra-lab/)