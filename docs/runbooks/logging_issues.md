# Runbook: Logging Issues

## Detect

The following signals indicate potential logging issues:

- Missing log entries or gaps in expected log output
- Errors initializing logging system
- OpenTelemetry connection errors
- Excessive log volume
- Missing context in logs
- Permission issues writing to log files

## Diagnose

### Check Logging Configuration

1. Verify the logging level:
   ```bash
   # Check the current logging configuration
   zcp logging test
   ```

2. Check environment variables:
   ```bash
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

3. Verify the CLI is initializing logging:
   ```bash
   # Run with debug logging
   zcp --log-level DEBUG doctor
   ```

### Check OpenTelemetry Connectivity

1. Test connectivity to the OTLP collector:
   ```bash
   # Test network connectivity
   curl -v $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

2. Verify the collector is running:
   ```bash
   # Check collector status (if running locally)
   systemctl status otel-collector
   ```

3. Check collector logs:
   ```bash
   # View collector logs
   journalctl -u otel-collector -f
   ```

### Check Log Output

1. Run a logging test with JSON output:
   ```bash
   zcp --json-logs logging test
   ```

2. Check log file permissions (if logging to file):
   ```bash
   ls -la /var/log/zcp/
   ```

## Mitigate

1. **If logs are missing:**
   Increase the log level to DEBUG:
   ```bash
   zcp --log-level DEBUG [command]
   ```

2. **If OpenTelemetry is failing:**
   Disable OTLP temporarily until the issue is resolved:
   ```bash
   # Run without OTLP
   zcp --log-level DEBUG [command]
   
   # Update environment variables
   unset OTEL_EXPORTER_OTLP_ENDPOINT
   ```

3. **If JSON logging is causing issues:**
   Revert to text logging:
   ```bash
   # Run without JSON logging
   zcp [command]
   ```

4. **If file permissions are the issue:**
   Fix file permissions:
   ```bash
   sudo mkdir -p /var/log/zcp/
   sudo chown $(whoami) /var/log/zcp/
   ```

5. **If log volume is excessive:**
   Increase the log level to reduce volume:
   ```bash
   zcp --log-level WARNING [command]
   ```

## Prevent

1. **Standardize logging configuration:**
   Create a central logging configuration file:
   ```
   # /etc/zcp/logging.conf
   level = INFO
   json_format = true
   otlp_enabled = true
   otlp_endpoint = http://otel-collector:4317
   ```

2. **Configure log rotation:**
   Set up logrotate for ZCP log files:
   ```
   # /etc/logrotate.d/zcp
   /var/log/zcp/*.log {
       daily
       rotate 7
       compress
       missingok
       notifempty
       create 0644 zcp zcp
   }
   ```

3. **Implement log monitoring:**
   Set up alerts for logging errors:
   ```sql
   SELECT count(*) FROM Log 
   WHERE logger LIKE 'zcp_%' AND level='ERROR' 
   FACET message
   SINCE 1 hour ago
   ```

4. **Regular log audits:**
   Periodically review logs for quality and completeness.

5. **Document logging standards:**
   Create and share logging guidelines for developers.
