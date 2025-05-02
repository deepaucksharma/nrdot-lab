# ADR 003: Linting Module Design

## Status

Accepted

## Context

The ZCP system needs a way to validate configuration files before deployment to catch common mistakes and ensure best practices. This helps prevent issues during rollout and reduces the risk of performance problems or missing data.

## Decision

We will implement a linting module with the following characteristics:

1. A rule-based architecture with pluggable rules
2. Three severity levels: ERROR, WARNING, INFO
3. Core rules for common issues:
   - YAML syntax validation
   - Integration name checking
   - Sample rate validation
   - Empty pattern detection
   - Discovery mode validation
4. Rule filtering to allow selective checks
5. CLI integration for easy validation
6. Schema validation of results for contract enforcement

Rules are registered in a central registry and can be enabled/disabled as needed.

## Consequences

### Positive

- Catches configuration errors before deployment
- Encourages best practices through rules
- Modular design allows easy addition of new rules
- CLI integration makes linting accessible to users
- Schema validation ensures consistent result structure

### Negative

- Rules need maintenance as agent config standards evolve
- May require updates when new agent versions change config format
- False positives possible for edge cases

## Reviewers

- ☑ SRE
- ☑ FinOps
- ☑ Sec-ops
