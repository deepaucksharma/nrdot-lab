# Extending the ProcessSample Lab

This guide explains how to extend the ProcessSample Optimization Lab with additional configurations, custom scenarios, and integrations.

## Adding Custom Scenarios

The lab supports multiple scenario configurations through Docker Compose override files. You can create your own scenarios by adding new override files.

### Creating a Custom Override

1. Create a new file in the `overrides/` directory:

```bash
touch overrides/my-custom-scenario.yml
```

2. Define your configuration changes:

```yaml
# overrides/my-custom-scenario.yml
version: '3.8'

services:
  infra:
    # Override infra service configuration
    environment:
      - CUSTOM_VARIABLE=value
    volumes:
      # Add or modify volume mounts
      - ./custom-config:/etc/newrelic-infra/custom:ro

  otel:
    # Override otel service configuration
    environment:
      - DEBUG=true
```

3. Run your custom scenario:

```bash
COMPOSE_FILE=docker-compose.yml:overrides/my-custom-scenario.yml make up
```

## Customizing Infrastructure Agent Configuration

You can extend the Infrastructure Agent configuration to test different settings:

### Testing Different Sample Rates

Modify `config/newrelic-infra.yml` to experiment with different sample rates:

```yaml
# For testing very low frequency collection (maximum cost savings)
metrics_process_sample_rate: 120  # 2 minutes between samples

# For testing higher frequency collection (better visibility)
metrics_process_sample_rate: 30   # 30 seconds between samples
```

### Adding Custom Process Filtering

Extend the process filtering configuration with more specific patterns:

```yaml
# Filter by process name pattern (Option 1: Map format)
exclude_matching_metrics:
  process.*.java: true
  process.*.node: true
  
# Filter by process name pattern (Option 2: Array format)
exclude_matching_metrics:
  - process.*.java
  - process.*.node
```

## Extending OpenTelemetry Collection

The OpenTelemetry Collector can be extended to collect additional metrics:

### Adding New Receivers

Modify `config/otel-config.yaml` to add new receivers:

```yaml
receivers:
  hostmetrics:
    collection_interval: 10s
    scrapers:
      # Add CPU load scraper
      load:
      # Add network statistics
      network:
      # Add process scraper (alternative to ProcessSample)
      process:
        mute_process_user_error: true
        mute_process_command_error: true
```

### Configuring Additional Exporters

Add new exporters to send metrics to other destinations:

```yaml
exporters:
  otlp:
    endpoint: "otlp.nr-data.net:4317"
    headers:
      api-key: "${NEW_RELIC_LICENSE_KEY}"
  
  # Add Prometheus exporter for local viewing
  prometheus:
    endpoint: 0.0.0.0:8889
```

## Creating Custom Load Patterns

The load generator can be customized to create specific patterns:

### Modifying the Load Generator

Edit the load generator configuration in `docker-compose.yml`:

```yaml
services:
  load:
    environment:
      # Number of processes to create
      - PROCESS_COUNT=10
      # CPU usage level (percentage)
      - CPU_LOAD=30
      # Memory usage in MB
      - MEMORY_MB=200
      # Process creation/termination interval
      - PROCESS_CHURN=60
```

### Creating a Custom Load Image

For more complex load patterns, you can create a custom load image:

1. Modify `load-image/Dockerfile` or create a new one
2. Implement your custom load pattern in the entrypoint script
3. Build and use your custom image

## Integrating with Alerting

Extend the lab to test alerting configurations:

### NRQL Alert Configuration

Create a New Relic alert condition for ProcessSample volume:

```
SELECT bytecountestimate()/1e9 as 'GB' 
FROM ProcessSample 
WHERE entityName = '${hostname}' 
SINCE 1 hour ago
```

Set a threshold to alert if the value exceeds your target optimization level.

## Running Long-Duration Experiments

For testing optimizations over longer periods:

### Creating a Multi-Day Test Script

```bash
#!/bin/bash
# long_duration_test.sh

# Run each scenario for 24 hours
DURATION_HOURS=24

# Standard scenario
COMPOSE_FILE=docker-compose.yml make up
echo "Running standard scenario for ${DURATION_HOURS} hours..."
sleep ${DURATION_HOURS}h
./scripts/validate_ingest.sh > results/standard_24h.log
make down

# Minimal mounts scenario
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
echo "Running minimal mounts scenario for ${DURATION_HOURS} hours..."
sleep ${DURATION_HOURS}h
./scripts/validate_ingest.sh > results/min_mounts_24h.log
make down

# Compare results
echo "Experiment complete. Results:"
cat results/standard_24h.log
cat results/min_mounts_24h.log
```

Make the script executable and run it:

```bash
chmod +x long_duration_test.sh
./long_duration_test.sh
```

## Extending Documentation

As you extend the lab, keep the documentation updated:

1. Document your custom scenarios in this file
2. Add NRQL queries for new metrics to `reference/nrql-cheatsheet.md`
3. Update configuration references as needed

## Contributing Extensions Back

If you develop useful extensions:

1. Create a clean branch with your changes
2. Test thoroughly and document your changes
3. Submit a pull request to the main repository
4. Include example results and benefits in your PR description