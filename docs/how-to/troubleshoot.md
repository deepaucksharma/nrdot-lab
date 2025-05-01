# Troubleshooting Guide

## Infrastructure Agent Issues

### No ProcessSample Events

1. Verify license key in `.env`
2. Check agent logs: `docker logs process_infra_1`
3. Ensure process metrics are enabled:
   ```yaml
   # config/newrelic-infra.yml
   enable_process_metrics: true
   ```

### Process Filtering Issues

Try one of these formats:

```yaml
# Option 1: Map Format
exclude_matching_metrics:
  process.*.*: true

# Option 2: Array Format
exclude_matching_metrics:
  - process.*.*
```

## Validation Script Issues

### API Connection Errors

1. Verify API key and account ID in `.env`
2. Ensure `jq` is installed
3. Check network connectivity to API

### No Data Available

1. Ensure lab has run for 5+ minutes
2. Verify containers are running: `docker ps`
3. Check logs: `make logs`

## OpenTelemetry Issues

### Missing Hostmetrics

1. Verify collector is running: `docker ps | grep otel`
2. Check logs: `docker logs process_otel_1`
3. Verify configuration in config/otel-config.yaml