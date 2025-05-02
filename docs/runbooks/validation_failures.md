# Runbook: Validation Failures

## Detect

The following signals indicate potential validation issues:

- `zcp validate check` command exits with non-zero status
- Validation events (`validate.result`) with `pass=false` in the event bus
- Significant deviation between expected and actual ingest rates (> 20%)
- Hosts consistently failing validation for more than 24 hours

## Diagnose

### Check Agent Status

1. Verify agent is running on affected hosts:
   ```bash
   systemctl status newrelic-infra
   ```

2. Check agent logs for errors:
   ```bash
   tail -100 /var/log/newrelic-infra/newrelic-infra.log | grep ERROR
   ```

3. Verify integration configuration is present:
   ```bash
   ls -la /etc/newrelic-infra/integrations.d/
   ```

### Check NRDB Data

1. Query for actual data ingest:
   ```
   FROM NrConsumption 
   SELECT sum(bytesIngested)/1024/1024/1024 as giBIngested 
   WHERE metricName='ProcessSample' AND hostname = '$HOST'
   SINCE 24 HOURS AGO
   TIMESERIES 1 hour
   ```

2. Look for gaps in the timeseries or unexpected drops in data volume.

3. Check for integration errors:
   ```
   FROM NrIntegrationError 
   SELECT count(*) 
   WHERE hostname = '$HOST' AND integrationName = 'nri-process-discovery'
   FACET message
   SINCE 24 HOURS AGO
   ```

### Check Configuration

1. Verify configuration checksum matches expected:
   ```bash
   sha256sum /etc/newrelic-infra/integrations.d/process-config.yaml
   ```

2. Check if process match patterns apply correctly:
   ```bash
   ps aux | grep -E 'pattern1|pattern2'
   ```

3. Check sample rate configuration:
   ```bash
   grep 'interval' /etc/newrelic-infra/integrations.d/process-config.yaml
   ```

## Mitigate

1. **If agent is not running:**
   ```bash
   systemctl restart newrelic-infra
   ```

2. **If configuration is missing or incorrect:**
   ```bash
   # Re-run rollout for affected hosts
   zcp rollout execute --hosts problem-host.example.com --config correct-config.yaml
   ```

3. **If filter patterns aren't matching processes:**
   Update the preset with appropriate patterns and re-run wizard:
   ```bash
   # Edit preset file
   vim <preset-path>/java_heavy.yaml
   
   # Re-run wizard and rollout
   zcp wizard --preset java_heavy --rollout --hosts affected-hosts.txt
   ```

4. **If data shows up in NRDB but validation still fails:**
   Adjust threshold to better match actual environment:
   ```bash
   zcp validate check --hosts affected-hosts.txt --expected 15.0 --threshold 0.25
   ```

## Prevent

1. **Improve presets:**
   - Use NRDB histogram data to create more accurate base estimates
   - Add more process patterns for better coverage
   - Adjust sample rates based on validated results

2. **Add monitoring:**
   - Create alert condition on validation failures
   - Monitor data gaps or drops in process sample ingest
   - Track validation success rate over time

3. **Improve pre-rollout checks:**
   - Add dry-run validation mode
   - Add preset verification against historical data
   - Create dashboard to track validation success rates
