# New Relic Infrastructure Agent Configuration Reference

This page documents the New Relic Infrastructure Agent configuration used in the ProcessSample Optimization Lab, with explanations of key settings and their impact on data collection and cost.

## Configuration File

The Infrastructure Agent configuration is located at `config/newrelic-infra.yml`. This file controls how the Infrastructure Agent collects and reports data to New Relic.

## Core Configuration

```yaml
--8<-- "config/newrelic-infra.yml"
```

## Key Settings Explained

### License Key

```yaml
license_key: 0123456789abcdef0123456789abcdef01234567
```

The license key authenticates your Infrastructure Agent with New Relic. In the actual lab, this is typically replaced with an environment variable reference like `${NEW_RELIC_LICENSE_KEY}` to use the value from your `.env` file.

### Process Metrics Collection

```yaml
enable_process_metrics: true
```

This setting enables the collection of ProcessSample events. Setting this to `false` would completely disable process monitoring.

### Sample Rate Configuration

```yaml
metrics_process_sample_rate: 60
```

**This is the most critical setting for ProcessSample optimization.** It controls how frequently the Infrastructure Agent collects process metrics:

| Value (seconds) | Impact on Data Volume | Observability Impact |
|-----------------|----------------------|---------------------|
| 20 (default)    | Baseline (highest)    | Highest frequency   |
| 30              | ~33% reduction        | Minor impact        |
| 60 (recommended)| ~67% reduction        | Balanced            |
| 120             | ~83% reduction        | Significant impact  |

Increasing this value directly reduces the number of ProcessSample events generated.

### Command Line Collection

```yaml
collect_process_commandline: false
```

This setting disables the collection of full command line arguments for processes. This reduces the size of each ProcessSample event and can help with both cost optimization and security (by not collecting potentially sensitive command line arguments).

### Process Filtering

```yaml
exclude_matching_metrics:
  process.name: ["systemd"]
  process.executable: ["/usr/bin/containerd", "/usr/sbin/cron"]
```

This configuration excludes specific processes from being monitored, based on process name or executable path. This reduces the volume of ProcessSample events by filtering out less important processes.

The format for process filtering can vary depending on your Infrastructure Agent version:

**Modern Format (shown above):**
```yaml
exclude_matching_metrics:
  process.name: ["systemd", "cron"]
  process.executable: ["/usr/bin/containerd"]
```

**Legacy Format - Option 1 (Map):**
```yaml
exclude_matching_metrics:
  process.*.*: true
```

**Legacy Format - Option 2 (Array):**
```yaml
exclude_matching_metrics:
  - process.*.*
```

## Advanced Settings

The Infrastructure Agent supports additional configuration options not used in this lab:

### Inventory Collection

```yaml
# Not included in basic configuration
strip_command_line: true                # Redact sensitive info from command lines
inventory_cache_enabled: true           # Cache inventory data to reduce CPU usage
```

### Network Configuration

```yaml
# Not included in basic configuration
proxy: http://user:pass@proxy.example.com:8080  # Use proxy for all communication
ignore_system_proxy: false                      # Ignore system proxy settings
```

### Security Considerations

```yaml
# Not included in basic configuration
passthrough_environment: ["SPECIFIC_ENV_VAR"]   # Control environment variable visibility
```

## Common Modifications

### For Maximum Cost Savings

```yaml
metrics_process_sample_rate: 120              # 2 minutes between samples
collect_process_commandline: false            # Don't collect command lines
exclude_matching_metrics:
  process.name: ["systemd", "cron", "sshd", "bash", "sh", "docker", "containerd"]
  process.executable: ["/usr/bin/containerd", "/usr/sbin/cron", "/usr/bin/dockerd"]
```

### For Better Security

```yaml
metrics_process_sample_rate: 60               # 1 minute between samples
collect_process_commandline: false            # Don't collect command lines
strip_command_line: true                      # Strip sensitive info from any command lines
```

### For Enhanced Visibility (Higher Cost)

```yaml
metrics_process_sample_rate: 30               # 30 seconds between samples
collect_process_commandline: true             # Include command lines for better debugging
```

## Troubleshooting Configuration Issues

If you encounter configuration errors:

1. Verify YAML syntax is correct with no indentation issues
2. Check that the license key is valid
3. Confirm that your agent version supports the configuration format you're using

For more details on troubleshooting, see the [Troubleshooting Guide](../how-to/troubleshoot.md).