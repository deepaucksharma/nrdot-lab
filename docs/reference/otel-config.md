# OpenTelemetry Configuration Reference

## Complete Configuration

```yaml
--8<-- "config/otel-config.yaml"
```

## Key Components

### Host Metrics Receiver

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
```

Collects system metrics at 10-second intervals:
- CPU usage
- Memory usage
- Disk I/O
- Filesystem usage
- Network activity
- System load

### Docker Stats Receiver

```yaml
receivers:
  docker_stats:
    endpoint: "unix:///var/run/docker.sock"
    collection_interval: 10s
```

Collects container metrics (requires Docker socket access):
- Container CPU usage
- Container memory usage
- Container network I/O
- Container block I/O

## Configuration Options

### Metrics Filtering

```yaml
filter/core-metrics:
  metrics:
    include:
      match_type: regexp
      metric_names: ["^system\\.(cpu|memory|disk|filesystem|network|load)\\..*"]
```

Controls which metrics are collected and sent to New Relic.

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