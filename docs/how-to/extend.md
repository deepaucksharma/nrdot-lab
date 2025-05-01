# Extending the Lab

## Custom Scenarios

Create new scenarios with Docker Compose override files:

1. Create a new override file:

```bash
touch overrides/my-custom-scenario.yml
```

2. Define configuration:

```yaml
# overrides/my-custom-scenario.yml
version: '3.8'
services:
  infra:
    environment:
      - CUSTOM_VARIABLE=value
    volumes:
      - ./custom-config:/etc/newrelic-infra/custom:ro
```

3. Run your scenario:

```bash
COMPOSE_FILE=docker-compose.yml:overrides/my-custom-scenario.yml make up
```

## Customizing Infrastructure Agent

### Sample Rate Adjustments

```yaml
# config/newrelic-infra.yml
# Lower frequency (max savings)
metrics_process_sample_rate: 120  # 2 minutes

# Higher frequency (better visibility)
metrics_process_sample_rate: 30   # 30 seconds
```

### Custom Process Filtering

```yaml
# Map format
exclude_matching_metrics:
  process.*.java: true
  process.*.node: true
  
# Array format
exclude_matching_metrics:
  - process.*.java
  - process.*.node
```

## Extending OpenTelemetry Collection

Add new receivers:

```yaml
# config/otel-config.yaml
receivers:
  hostmetrics:
    collection_interval: 10s
    scrapers:
      load:
      network:
      process:
        mute_process_user_error: true
        mute_process_command_error: true
```

## Custom Load Patterns

Modify load generator settings:

```yaml
# docker-compose.yml
services:
  load:
    environment:
      - PROCESS_COUNT=10
      - CPU_LOAD=30
      - MEMORY_MB=200
      - PROCESS_CHURN=60
```

## NRQL Alert Configuration

```sql
SELECT bytecountestimate()/1e9 as 'GB' 
FROM ProcessSample 
WHERE entityName = '${hostname}' 
SINCE 1 hour ago
```

Set a threshold to alert if the value exceeds your target.