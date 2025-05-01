# OpenTelemetry Collector Configuration Reference

This page documents the OpenTelemetry Collector configuration used in the ProcessSample Optimization Lab, with explanations of key components and how they work together to provide comprehensive metrics while optimizing ProcessSample costs.

## Configuration File

The OpenTelemetry Collector configuration is located at `config/otel-config.yaml`. This file defines what metrics are collected, how they're processed, and where they're sent.

## Complete Configuration

```yaml
--8<-- "config/otel-config.yaml"
```

## Configuration Components

The OpenTelemetry configuration consists of several main sections:

1. **Extensions** - Additional functionalities for the collector
2. **Receivers** - Data collection components
3. **Processors** - Data transformation and filtering
4. **Exporters** - Destinations for the data
5. **Service** - Pipelines connecting the components

Let's examine each section in detail:

### Extensions

```yaml
extensions:
  health_check: {}
```

Extensions provide additional functionality to the collector. The `health_check` extension enables a health endpoint that can be used to verify the collector is running properly.

### Receivers

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
  docker_stats:
    endpoint: "unix:///var/run/docker.sock"
    collection_interval: 10s
```

Receivers collect metrics from various sources:

#### Host Metrics Receiver

The `hostmetrics` receiver collects system-level metrics at a 10-second interval, providing high-frequency data about:

- **CPU**: Usage, time, utilization by state
- **Memory**: Usage, available memory, swap
- **Disk**: I/O operations, bytes read/written, operation time
- **Filesystem**: Usage, available space, inodes
- **Network**: Packets sent/received, bytes sent/received, errors
- **Load**: System load averages (1m, 5m, 15m)

These metrics provide most of the system-level visibility normally derived from ProcessSample events, but with less data volume.

#### Docker Stats Receiver

The `docker_stats` receiver collects metrics from Docker containers, including:

- Container CPU usage
- Container memory usage
- Container network I/O
- Container block I/O

This receiver requires access to the Docker socket, which is provided by a volume mount in the `docker-stats.yml` override file.

### Processors

```yaml
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
```

Processors transform and filter metrics:

- **memory_limiter**: Prevents the collector from using too much memory
- **filter/core-metrics**: Only includes system metrics matching the specified pattern
- **batch**: Batches metrics for more efficient transmission

### Exporters

```yaml
exporters:
  otlp:
    endpoint: "otlp.nr-data.net:4317"
    headers:
      api-key: "${NEW_RELIC_LICENSE_KEY}"
```

Exporters send metrics to their destinations:

- **otlp**: Sends metrics to New Relic using the OpenTelemetry Protocol (OTLP)
- The `api-key` header authenticates with New Relic using your license key

### Service

```yaml
service:
  extensions: [health_check]
  pipelines:
    metrics:
      receivers: [hostmetrics, docker_stats]
      processors: [memory_limiter, filter/core-metrics, batch]
      exporters: [otlp]
```

The service section defines the pipelines that connect components:

- Enables the `health_check` extension
- Creates a metrics pipeline that:
  1. Collects metrics from `hostmetrics` and `docker_stats` receivers
  2. Processes them through `memory_limiter`, `filter/core-metrics`, and `batch` processors
  3. Exports them to New Relic via the `otlp` exporter

## Key Configuration Options

### Collection Interval

```yaml
collection_interval: 10s
```

This setting controls how frequently metrics are collected. A shorter interval (like 10s) provides more granular data but increases data volume. This complements the reduced ProcessSample frequency (60s) by providing high-frequency system metrics while process metrics are collected less frequently.

### Include/Exclude Filters

```yaml
metrics:
  include:
    match_type: regexp
    metric_names: ["^system\\.(cpu|memory|disk|filesystem|network|load)\\..*"]
```

These filters control which metrics are processed. This configuration includes only system metrics, filtering out any other metrics that might be collected.

## Common Modifications

### For Maximum Performance Visibility

```yaml
receivers:
  hostmetrics:
    collection_interval: 5s  # More frequent collection
    scrapers:
      # Add detailed CPU metrics
      cpu:
        metrics:
          system.cpu.time:
            enabled: true
      # Include paging and swap metrics
      memory:
        metrics:
          system.memory.usage:
            enabled: true
          system.memory.swap.usage:
            enabled: true
```

### For Minimal Data Volume

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s  # Less frequent collection
    scrapers:
      # Only essential metrics
      cpu:
      memory:
```

### For Container Monitoring

```yaml
receivers:
  docker_stats:
    endpoint: "unix:///var/run/docker.sock"
    collection_interval: 10s
    timeout: 20s
    api_version: 1.24
    container_labels_to_metric_labels:
      com.example.label.name: container_label_name
```

## Docker Stats Configuration

The `docker_stats` receiver requires:

1. Access to the Docker socket:
   ```yaml
   # In docker-compose.override.yml or similar
   volumes:
     - /var/run/docker.sock:/var/run/docker.sock:ro
   ```

2. Inclusion in the metrics pipeline:
   ```yaml
   service:
     pipelines:
       metrics:
         receivers: [hostmetrics, docker_stats]
   ```

**Security Note**: Mounting the Docker socket increases the attack surface of your container. Use with caution and only when container metrics are required.

## Troubleshooting

If metrics aren't appearing in New Relic:

1. Check that the collector is running:
   ```bash
   docker ps | grep otel
   ```

2. Verify the license key is correct in your `.env` file

3. Check the collector logs for errors:
   ```bash
   docker logs infra-lab-otel-1
   ```

4. Verify network connectivity to the New Relic endpoint:
   ```bash
   curl -v otlp.nr-data.net:4317
   ```

For more troubleshooting steps, see the [Troubleshooting Guide](../how-to/troubleshoot.md).