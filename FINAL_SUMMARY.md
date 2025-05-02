# ProcessSample Optimization Lab - Summary

## Purpose

This lab environment helps optimize New Relic ProcessSample ingest costs by ~70% while maintaining full observability capabilities. It provides a containerized testing environment with validation tools.

## Core Components

- **Infrastructure Agent**: Collects ProcessSample data with optimized configuration
- **OpenTelemetry Collector**: Provides system metrics via hostmetrics receiver
- **Synthetic Load Generator**: Creates test processes with configurable load patterns
- **Validation Tools**: Measures actual cost reduction and observability impact

## Key Features

- **Sample Rate Control**: Configure collection intervals from 20s to 120s
- **Process Filtering**: Multiple strategies from no filtering to aggressive filtering
- **OpenTelemetry Integration**: Configurable collection intervals (5s to 30s)
- **Docker Stats**: Optional container metrics collection
- **Cross-platform Support**: Works on Linux, macOS, and Windows
- **Template-based Configuration**: Centralized, easy-to-modify templates

## Command Interfaces

- **Linux/macOS**: Makefile with intuitive commands
- **Windows**: PowerShell script (process-lab.ps1) with matching functionality

## Usage Examples

```bash
# Linux/macOS
make up                     # Start with default configuration
make filter-aggressive      # Use aggressive process filtering
make validate-json          # Validate and output JSON results

# Windows
.\process-lab.ps1 up                # Start with default configuration
.\process-lab.ps1 filter-aggressive # Use aggressive process filtering
.\process-lab.ps1 validate -Format json # Validate and output JSON results
```

## Cost Optimization Results

| Configuration | Sample Rate | Filtering | Reduction |
|---------------|-------------|-----------|-----------|
| Default NR | 20s | None | Baseline |
| Basic | 60s | None | ~67% |
| Standard | 60s | Standard | ~70% |
| Aggressive | 60s | Aggressive | ~75% |
| Maximum | 120s | Aggressive | ~85% |

These optimizations maintain essential visibility while significantly reducing ingest costs.
