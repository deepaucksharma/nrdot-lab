# OpenTelemetry Configuration Reference

## Core Configuration

```yaml
receivers:
  hostmetrics:
    collection_interval: 10s
    scrapers:
      cpu:
      memory:
      disk:
      filesystem:
      network:
      load:

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
  filter/core-metrics:
    metrics:
      include:
        match_type: regexp
        metric_names: ["^system\\.(cpu|memory|disk|filesystem|network|load)\\..*"]
  batch: {}

exporters:
  otlp:
    endpoint: "otlp.nr-data.net:4317"
    headers:
      api-key: "${NEW_RELIC_LICENSE_KEY}"

service:
  pipelines:
    metrics:
      receivers: [hostmetrics]
      processors: [memory_limiter, filter/core-metrics, batch]
      exporters: [otlp]
```

## Key Components

### Host Metrics Receiver

Collects system metrics at 10-second intervals:
- CPU usage
- Memory usage
- Disk I/O
- Filesystem usage
- Network activity
- System load

### Docker Stats Receiver (Optional)

For container metrics (requires Docker socket access):

```yaml
receivers:
  docker_stats:
    endpoint: "unix:///var/run/docker.sock"
    collection_interval: 10s
```

Add to service pipeline:
```yaml
service:
  pipelines:
    metrics:
      receivers: [hostmetrics, docker_stats]
```

## Configuration Options

### Collection Frequency

```yaml
collection_interval: 10s  # Default: high frequency
collection_interval: 30s  # Lower frequency, less data
```

### Metric Filtering

```yaml
# Include only specific metrics
filter/core-metrics:
  metrics:
    include:
      match_type: regexp
      metric_names: ["^system\\.(cpu|memory)\\..*"]
```

## Common Configurations

### High-Resolution Monitoring

```yaml
receivers:
  hostmetrics:
    collection_interval: 5s
    scrapers:
      cpu:
      memory:
      disk:
      load:
```

### Minimal Volume

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu:
      memory:
```

## Troubleshooting

If metrics aren't appearing:

1. Check collector status: `docker ps | grep otel`
2. Verify license key in `.env`
3. Check logs: `docker logs process_otel_1`