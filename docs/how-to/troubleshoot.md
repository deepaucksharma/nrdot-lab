# Troubleshooting the ProcessSample Lab

This guide helps resolve common issues you might encounter while working with the ProcessSample Optimization Lab.

## Security and Seccomp Issues

### "seccomp blocked syscall" Errors

**Symptoms**:
- Container exits unexpectedly
- Logs show "seccomp blocked syscall" errors

**Solutions**:

1. Temporarily disable seccomp to identify the issue:
   ```bash
   COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
   ```

2. Identify the blocked syscalls from the logs:
   ```bash
   make logs
   ```

3. Add the required syscalls to `profiles/seccomp-nr.json`

### Understanding Seccomp Profiles

The seccomp profile restricts container syscalls to a minimal allowed set. This significantly reduces the attack surface by limiting which system calls containers can make.

To view the current seccomp profile:

```bash
cat profiles/seccomp-nr.json
```

## Infrastructure Agent Issues

### Missing Process Metrics

**Symptoms**:
- No ProcessSample events in New Relic
- No reduction shown in `make validate`

**Solutions**:

1. Verify license key in `.env`:
   ```bash
   grep NEW_RELIC_LICENSE_KEY .env
   ```

2. Check for errors in Infrastructure Agent logs:
   ```bash
   make logs
   ```

3. Ensure process metrics are enabled in configuration:
   ```yaml
   # config/newrelic-infra.yml
   enable_process_metrics: true
   ```

### Process Filtering Configuration Issues

**Symptoms**:
- Infrastructure agent fails to start or errors in logs
- Filtering doesn't seem to be working

**Solutions**:

The exact format for process filtering depends on your New Relic Infrastructure Agent version. Try each of these formats:

**Option 1: Map Format**
```yaml
exclude_matching_metrics:
  process.*.*: true
```

**Option 2: Array Format**
```yaml
exclude_matching_metrics:
  - process.*.*
```

**Troubleshooting Format Issues**:
- If you see "cannot unmarshal !!bool `true` into []string", switch from map format to array format.
- If you see "cannot unmarshal !!seq into config.ExcludeMetricsMap", switch from array format to map format.
- If you continue to have issues, remove the exclude_matching_metrics section altogether.

## Validation Script Errors

### API Connection Issues

**Symptoms**:
- `make validate` fails with API errors

**Solutions**:

1. Verify API key and account ID in `.env`:
   ```bash
   grep NEW_RELIC_API_KEY .env
   grep NR_ACCOUNT_ID .env
   ```

2. Ensure `jq` is installed:
   ```bash
   jq --version
   ```

3. Check network connectivity to New Relic API:
   ```bash
   curl -I https://api.newrelic.com/graphql
   ```

### No Data Available

**Symptoms**:
- `make validate` returns zero or no data

**Solutions**:

1. Ensure the lab has been running for at least 5 minutes
2. Verify the Infrastructure agent is running:
   ```bash
   docker ps | grep infra
   ```
3. Check the logs for any errors:
   ```bash
   make logs
   ```

## Docker and Container Issues

### Docker Socket Access Issues

**Symptoms**:
- When using container metrics, errors accessing docker.sock

**Solutions**:

1. Verify your user has permissions to access docker.sock:
   ```bash
   ls -la /var/run/docker.sock
   ```

2. On some systems, you may need to add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   # You'll need to log out and back in for this to take effect
   ```

3. If using Docker Desktop, ensure file sharing is enabled for the relevant directories

### Volume Mount Issues

**Symptoms**:
- Container fails to start with errors about mounts
- Missing metrics that require filesystem access

**Solutions**:

1. For Docker Desktop users, verify the path is shared in Docker preferences
2. Try the minimal mounts configuration:
   ```bash
   COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
   ```
3. Check container status and logs:
   ```bash
   docker ps -a
   docker logs infra-lab-infra-1
   ```

## OpenTelemetry Issues

### Missing Hostmetrics

**Symptoms**:
- No hostmetrics data in New Relic while ProcessSample data is visible

**Solutions**:

1. Verify the OpenTelemetry collector is running:
   ```bash
   docker ps | grep otel
   ```

2. Check collector logs:
   ```bash
   docker logs infra-lab-otel-1
   ```

3. Verify the receiver configuration:
   ```yaml
   # config/otel-config.yaml
   receivers:
     hostmetrics:
       collection_interval: 10s
   ```

4. Ensure the pipeline is configured correctly:
   ```yaml
   service:
     pipelines:
       metrics:
         receivers: [hostmetrics]
         # ...
   ```

## Troubleshooting on Windows

If you're running the lab on Windows, there are some additional considerations:

1. Use the Windows-specific validation script:
   ```bash
   scripts\validate_ingest_windows.bat
   ```

2. For Docker Desktop users, ensure Linux containers mode is enabled

3. Path formatting may differ - use Windows paths in your configurations:
   ```yaml
   # Example for a Windows path
   volumes:
     - D:\NewRelic\Infra_plus\process\config:/etc/newrelic-infra.yml
   ```

## Getting Additional Help

If you're still experiencing issues:

1. Collect the full logs:
   ```bash
   make logs > lab-debug.log
   ```

2. Run the validation script with verbose mode:
   ```bash
   ./scripts/validate_ingest.sh -v > validation-debug.log
   ```

3. Create an issue on GitHub with both log files attached