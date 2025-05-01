# Infrastructure Agent Configuration Reference

## Core Configuration

```yaml
license_key: ${NEW_RELIC_LICENSE_KEY}
enable_process_metrics: true
metrics_process_sample_rate: 60
collect_process_commandline: false
```

## Key Settings

### Process Sample Rate

```yaml
metrics_process_sample_rate: 60
```

This controls collection frequency:

| Value (seconds) | Data Volume Impact | Observability Impact |
|-----------------|-------------------|---------------------|
| 20 (default)    | Baseline          | Highest frequency   |
| 60 (recommended)| ~67% reduction    | Balanced            |
| 120             | ~83% reduction    | Lower visibility    |

### Process Filtering

**Modern Format:**
```yaml
exclude_matching_metrics:
  process.name: ["systemd"]
  process.executable: ["/usr/bin/containerd"]
```

**Legacy Format - Map:**
```yaml
exclude_matching_metrics:
  process.*.*: true
```

**Legacy Format - Array:**
```yaml
exclude_matching_metrics:
  - process.*.*
```

## Configuration Presets

### Maximum Cost Savings

```yaml
metrics_process_sample_rate: 120
collect_process_commandline: false
exclude_matching_metrics:
  process.name: ["systemd", "cron", "sshd", "bash", "sh", "docker"]
```

### Enhanced Security

```yaml
metrics_process_sample_rate: 60
collect_process_commandline: false
strip_command_line: true
```

### Enhanced Visibility (Higher Cost)

```yaml
metrics_process_sample_rate: 30
collect_process_commandline: true
```

## Troubleshooting

If configuration errors occur:

1. Verify YAML syntax and indentation
2. Check license key validity
3. Confirm agent version supports your configuration format