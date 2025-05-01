# New Relic ProcessSample Optimization Lab

[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://deepaucksharma.github.io/infra-lab/)
[![CI Status](https://img.shields.io/github/actions/workflow/status/deepaucksharma/infra-lab/ci.yml?branch=master&label=ci)](https://github.com/deepaucksharma/infra-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability. Reduce ingest costs by ~70% while maintaining essential visibility.

## Core Features

- **Sample Rate Optimization**: 60s interval (vs 20s default)
- **Smart Process Filtering**: Exclude non-essential processes 
- **Complementary Metrics**: High-frequency system data via OpenTelemetry
- **Real-time Validation**: Measure actual ingest reduction

## Quick Start

```bash
# Clone repository
git clone https://github.com/deepaucksharma/infra-lab.git
cd infra-lab

# Configure credentials
cp .env.example .env
# Edit .env with your NR license key, API key, and account ID

# Start the lab
make up

# Monitor logs
make logs

# Validate results (after 5-10 minutes)
make validate
```

## Key Components

- **Infrastructure Agent**: Collects ProcessSample with optimized configuration
- **OpenTelemetry Collector**: Provides system metrics via hostmetrics receiver
- **Synthetic Load Generator**: Creates realistic process patterns for testing

## Available Scenarios

| Scenario | Command | Purpose |
|----------|---------|---------|
| Default | `make up` | Default optimization |
| Docker Stats | `make docker-stats` | Add container metrics |

## Prerequisites

- Docker Engine and Docker Compose v2+
- `make` and `jq` utilities
- New Relic account with license key, API key, and account ID

## Documentation

[View the complete documentation](https://deepaucksharma.github.io/infra-lab/)