# New Relic ProcessSample Optimization Lab

[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://deepaucksharma.github.io/infra-lab/)
[![CI Status](https://img.shields.io/github/actions/workflow/status/deepaucksharma/infra-lab/ci.yml?branch=main&label=ci)](https://github.com/deepaucksharma/infra-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment that reduces New Relic ProcessSample ingest costs by ~70% without sacrificing observability.

## Core Features

- **Sample Rate Optimization**: Configurable interval (default: 60s vs standard 20s)
- **Smart Process Filtering**: Multiple filtering strategies to exclude non-essential processes
- **Complementary Metrics**: High-frequency system data via OpenTelemetry
- **Real-time Validation**: Built-in tools to measure actual ingest reduction
- **Cross-platform Support**: Works on Linux, macOS, and Windows

## Quick Start

```bash
# Clone repository
git clone https://github.com/deepaucksharma/infra-lab.git
cd infra-lab

# Configure credentials
cp .env.example .env
# Edit .env with your NR license key, API key, and account ID

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
# Edit .env with your NR license key, API key, and account ID

# Generate configurations
.\process-lab.ps1 generate-configs

# Start the lab with optimized settings
.\process-lab.ps1 up

# Validate results (after 5-10 minutes)
.\process-lab.ps1 validate
```

## Available Configurations

| Configuration | Command | Purpose |
|---------------|---------|---------|
| Standard | `make up` | Default optimization |
| Minimal Mounts | `make minimal` | Minimal filesystem access |
| Docker Stats | `make docker-stats` | Add container metrics |
| Secure Mode | `make secure-mode` | Toggle secure execution |

## Filter Types

| Filter | Command | Description |
|--------|---------|-------------|
| None | `make filter-none` | No filtering (baseline) |
| Standard | `make filter-standard` | Basic system process filtering |
| Aggressive | `make filter-aggressive` | Maximum filtering (recommended) |
| Targeted | `make filter-targeted` | Whitelist approach - only include specified processes |

## Validation & Visualization

```bash
# Validate current ingest rates
make validate          # Text output
make validate-json     # JSON output
make validate-csv      # CSV output for analysis

# Generate visualizations from results
make visualize
```

## Prerequisites

- Docker Engine and Docker Compose v2+
- Python 3.6+ (for visualization)
- New Relic account with license key, API key, and account ID

## Documentation

Refer to the [docs](./docs) directory for detailed documentation.

## License

[MIT License](LICENSE)