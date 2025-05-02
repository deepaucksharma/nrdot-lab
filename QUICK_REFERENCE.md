# ProcessSample Lab Quick Reference

## Core Commands

### Linux/macOS
```bash
make up                     # Start with standard settings
make down                   # Stop lab
make logs                   # View logs
make validate               # Check results
make generate-configs       # Generate configuration files
```

### Windows
```powershell
.\process-lab.ps1 up        # Start with standard settings
.\process-lab.ps1 down      # Stop lab
.\process-lab.ps1 logs      # View logs
.\process-lab.ps1 validate  # Check results
.\process-lab.ps1 generate-configs  # Generate configuration files
```

## Configuration Options

### Filter Types
```bash
# Linux/macOS
make filter-none            # No filtering
make filter-standard        # Basic filtering
make filter-aggressive      # Maximum filtering
make filter-targeted        # Whitelist filtering

# Windows
.\process-lab.ps1 filter-none
.\process-lab.ps1 filter-standard
.\process-lab.ps1 filter-aggressive
.\process-lab.ps1 filter-targeted
```

### Sample Rates
```bash
# Linux/macOS
make sample-20              # 20s interval (default NR)
make sample-60              # 60s interval (recommended)
make sample-120             # 120s interval (maximum savings)

# Windows
.\process-lab.ps1 sample-20
.\process-lab.ps1 sample-60
.\process-lab.ps1 sample-120
```

### Variants
```bash
# Linux/macOS
make docker-stats           # Enable Docker metrics collection
make minimal-mounts         # Use minimal filesystem mounts
make secure-off             # Disable seccomp security profiles

# Windows
.\process-lab.ps1 docker-stats
.\process-lab.ps1 minimal-mounts
.\process-lab.ps1 secure-off
```

## Validation
```bash
# Linux/macOS
make validate               # Text output
make validate-json          # JSON output
make validate-csv           # CSV output

# Windows
.\process-lab.ps1 validate -Format text
.\process-lab.ps1 validate -Format json
.\process-lab.ps1 validate -Format csv
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| NEW_RELIC_LICENSE_KEY | - | Your New Relic license key |
| NEW_RELIC_API_KEY | - | Your New Relic API key |
| NR_ACCOUNT_ID | - | Your New Relic account ID |
| FILTER_TYPE | standard | Filter type to use |
| SAMPLE_RATE | 60 | ProcessSample interval in seconds |
| OTEL_INTERVAL | 10s | OpenTelemetry collection interval |
| STRESS_CPU | 2 | Number of CPU cores for load testing |
| STRESS_MEM | 128M | Memory allocation for load testing |
| STRESS_IO | 0 | IO workers for load testing |

## Results Directory Structure
```
results/
  YYYYMMDD_HHMMSS/         # Timestamp of test run
    scenario-name.json     # Validation results
    docker_stats.txt       # Resource usage statistics
  visualizations/          # Contains generated charts
```

## Recommended Configuration
- Sample Rate: 60 seconds
- Filter Type: Aggressive
- OTel Interval: 10 seconds
- Expected Reduction: ~75%
