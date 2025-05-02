# ADR 002: Validation Module Design

## Status

Accepted

## Context

The ZCP system needs a way to validate that deployed configurations are working as expected by comparing estimated data ingest with actual data usage. This requires interacting with the New Relic Database (NRDB) to query metrics data, handling potential failures gracefully, and providing actionable validation results.

## Decision

We will implement a validation module with the following characteristics:

1. A robust NRDB client with circuit breaker pattern to handle intermittent NRDB failures
2. Support for validation of multiple hosts in a single operation
3. Configurable thresholds for allowable deviations
4. Comprehensive validation results with per-host details
5. Schema validation of results for contract enforcement
6. CLI integration for easy validation operations

The circuit breaker pattern will prevent cascading failures during NRDB outages, while still allowing retries after a cooldown period.

## Consequences

### Positive

- Provides a way to verify that configurations are working correctly
- Helps identify discrepancies between estimated and actual data usage
- Robust against NRDB outages or intermittent issues
- Schema validation ensures consistent result structure
- CLI integration makes validation accessible to users

### Negative

- Depends on NRDB availability for full functionality
- Requires API keys with appropriate permissions
- Validation results may vary based on time window

## Reviewers

- ☑ SRE
- ☑ FinOps
- ☑ Sec-ops
