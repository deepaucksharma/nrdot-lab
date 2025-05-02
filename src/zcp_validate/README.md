# ZCP Validation Module

The validation module compares expected data ingest with actual data from NRDB to verify that configurations are working correctly.

## Features

- **NRDB Integration**: Queries New Relic Database (NRDB) for actual data ingest metrics
- **Circuit Breaker**: Prevents overwhelming NRDB during outages
- **Threshold-Based Validation**: Configurable thresholds for allowable deviations
- **Detailed Results**: Per-host validation details with human-readable messages
- **Schema Validation**: Ensures consistent result structure
- **CLI Integration**: Easy validation through command-line interface

## Usage

### CLI Example

```bash
# Validate configuration by comparing expected vs. actual ingest
zcp validate check --hosts host1.example.com,host2.example.com --expected 10.5 --threshold 0.2
```

### Programmatic Example

```python
from zcp_validate.models import ValidationJob
from zcp_validate.validator import Validator

# Create validation job
job = ValidationJob(
    hosts=["host1.example.com", "host2.example.com"],
    expected_gib_day=10.5,
    confidence=0.8,
    threshold=0.2,
    timeframe_hours=24
)

# Create validator and execute validation
validator = Validator()
result = validator.validate(job)

# Use validation result
print(f"Validation result: {result.summary}")
for hostname, host_result in result.host_results.items():
    print(f"  {hostname}: {host_result.message}")
```

## Configuration

The module can be configured through environment variables:

- `NEW_RELIC_API_KEY`: API key for NRDB access
- `NEW_RELIC_ACCOUNT_ID`: New Relic account ID
- `NEW_RELIC_REGION`: Region (us or eu, default: us)
- `NEW_RELIC_TIMEOUT`: Query timeout in seconds (default: 30)

## Architecture

The validation module follows a layered architecture:

1. **NRDB Client**: Handles communication with NRDB API
2. **Validator**: Core validation logic
3. **Models**: Data structures for validation jobs and results
4. **CLI Interface**: Command-line integration

The circuit breaker pattern is implemented in the NRDB client to prevent overwhelming the API during outages. It automatically resets after a configurable cooldown period.

## Schema

Validation results follow the ValidationResult schema defined in schema/v1/ValidationResult.schema.json:

```json
{
  "pass_rate": 0.75,
  "overall_pass": false,
  "host_results": {
    "host1.example.com": {
      "hostname": "host1.example.com",
      "expected_gib_day": 10.0,
      "actual_gib_day": 12.5,
      "within_threshold": false,
      "deviation_percent": 25.0,
      "message": "FAIL: Actual ingest is 12.50 GiB/day, which is 25.0% higher than expected (10.00 GiB/day)"
    }
  }
}
```

## Testing

The module includes unit tests for validator functionality, with mock NRDB client to simulate various scenarios:

```bash
pytest tests/unit/validate/
```
