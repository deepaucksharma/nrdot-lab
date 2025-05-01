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

# Start the lab (with minimal filesystem access by default)
make up

# Validate results (after 5 minutes)
make validate
```

## Available Scenarios

| Scenario | Command | Purpose |
|----------|---------|---------|
| Default (Minimal) | `make up` | Default optimization with minimal mounts |
| Full Host Access | `make full-host` | Full filesystem access (less secure) |
| Docker Stats | `make docker-stats` | Add container metrics |
| Seccomp Off | `make seccomp-off` | Disable seccomp for troubleshooting |
| Enhanced Seccomp | `make seccomp-v2` | Use improved seccomp profile |

## Security Features

- Limited filesystem access by default (only `/proc` and `/sys`)
- Seccomp profile restricts allowed syscalls
- Read-only containers with minimal capabilities
- No hard-coded credentials

## Requirements

- Docker and Docker Compose v2
- `jq` for validation
- New Relic account with license key, API key, and account ID

## Documentation

[View the complete documentation](https://deepaucksharma.github.io/infra-lab/)