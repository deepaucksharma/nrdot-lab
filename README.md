# New Relic ProcessSample Optimization Lab

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability. Reduce ingest costs by ~70% while maintaining essential visibility.

## Core Optimization Strategies

- **Sample Rate Adjustment**: Configure intervals from 20s (default) to 60s (~67% reduction)
- **Process Filtering**: Multiple strategies to exclude non-essential processes (~5-10% additional reduction)
- **OpenTelemetry Integration**: Maintain high-frequency system visibility with minimal data volume

## Quick Start

```bash
# Clone repository
git clone https://github.com/deepaucksharma/infra-lab.git
cd infra-lab

# Configure credentials
cp .env.example .env
# Edit .env with your NR license key, API key, and account ID

# Start the lab with default settings (60s rate, standard filtering)
python scripts/unified/process_lab.py up

# Validate results (after 5-10 minutes)
python scripts/unified/process_lab.py validate
```

## Command Interface

The lab uses a unified Python-based command interface that works across all platforms:

```bash
# Start the lab with current settings
python scripts/unified/process_lab.py up

# Stop the lab
python scripts/unified/process_lab.py down

# View logs
python scripts/unified/process_lab.py logs

# Check ingestion reduction
python scripts/unified/process_lab.py validate --format json

# Remove all containers and volumes
python scripts/unified/process_lab.py clean

# Generate configuration files manually
python scripts/unified/process_lab.py generate-configs
```

## Configuration Options

All options can be provided as command-line arguments:

```bash
# Change filter type
python scripts/unified/process_lab.py up --filter-type aggressive

# Change sample rate
python scripts/unified/process_lab.py up --sample-rate 120

# Enable Docker metrics
python scripts/unified/process_lab.py up --docker-stats

# Combine multiple options
python scripts/unified/process_lab.py up --filter-type targeted --sample-rate 60 --docker-stats
```

### Filter Types

| Filter | Description | Reduction |
|--------|-------------|-----------|
| none | No filtering (baseline) | 0% |
| standard | Basic system process filtering | ~5% |
| aggressive | Maximum filtering | ~10% |
| targeted | Whitelist approach | Variable |

### Sample Rates

Set the `--sample-rate` parameter to the desired interval in seconds:

```bash
python scripts/unified/process_lab.py up --sample-rate 120  # 83% reduction from 20s default
python scripts/unified/process_lab.py up --sample-rate 60   # 67% reduction (recommended)
python scripts/unified/process_lab.py up --sample-rate 30   # 33% reduction
```

### OpenTelemetry Configuration

Control the OTel collection interval:

```bash
python scripts/unified/process_lab.py up --otel-interval 5s   # Higher frequency
python scripts/unified/process_lab.py up --otel-interval 10s  # Default
python scripts/unified/process_lab.py up --otel-interval 30s  # Lower overhead
```

## Testing Scenarios

The lab includes several pre-defined testing scenarios:

```bash
# Run baseline test (original settings)
python scripts/unified/process_lab.py baseline

# Run optimized lab configuration
python scripts/unified/process_lab.py lab-opt

# Test multiple sample rates sequentially
python scripts/unified/process_lab.py rate-sweep

# Test all filter types sequentially
python scripts/unified/process_lab.py filter-matrix
```

## Optimization Results

| Configuration | Sample Rate | Filtering | Reduction | Visibility Impact |
|---------------|-------------|-----------|-----------|-------------------|
| Default | 20s | None | 0% (baseline) | None |
| Basic | 60s | None | ~67% | Minimal |
| Standard | 60s | Standard | ~70% | Minimal |
| Aggressive | 60s | Aggressive | ~75% | Low |
| Maximum | 120s | Aggressive | ~85% | Moderate |

## Best Practices

- Start with standard filtering and 60s sample rate
- Monitor for 5-10 minutes, then use validation to check results
- If more reduction is needed, try aggressive filtering
- For maximum reduction, use 120s sample rate with aggressive filtering

## Architecture

The lab consists of three main components:

1. **Infrastructure Agent**: Collects ProcessSample events with optimized configuration
2. **OpenTelemetry Collector**: Provides system metrics via hostmetrics receiver
3. **Synthetic Load Generator**: Creates realistic process patterns for testing

## Configuration Details

All configurations are generated at runtime based on your settings:

- `config/newrelic-infra.yml` - Infrastructure agent configuration
- `config/otel-config.yaml` - OpenTelemetry collector configuration 
- `config/filter-definitions.yml` - Process filtering patterns

The configurations are fully customizable through filter definitions and environment variables.

## Prerequisites

- Docker Engine and Docker Compose v2+
- Python 3.6+
- New Relic account with license key, API key, and account ID

## License

[MIT License](LICENSE)