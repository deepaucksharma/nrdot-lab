# ZCP Project Documentation

This document serves as the central index for all ZCP project documentation.

## Quick Start

- [README.md](../README.md) - Project overview and quick start guide
- [CURRENT_STATUS.md](../CURRENT_STATUS.md) - Current project status and recent improvements
- [ROADMAP.md](../ROADMAP.md) - Project roadmap and milestone tracking

## Development

- [DEVELOPMENT.md](../DEVELOPMENT.md) - Development guidelines and workflow
- [FIXES.md](../FIXES.md) - Recent critical fixes and improvements

## Testing

- [TEST_IMPROVEMENT_PLAN.md](TEST_IMPROVEMENT_PLAN.md) - Comprehensive test implementation plan
- [TEST_STRATEGY.md](../TEST_STRATEGY.md) - Testing strategy and approach

## Architecture

### Architecture Decision Records (ADRs)

- [001-event-bus.md](adr/001-event-bus.md) - Event bus architecture and patterns
- [002-validation-module.md](adr/002-validation-module.md) - Validation module design
- [003-linting-module.md](adr/003-linting-module.md) - Linting module architecture
- [004-logging-module.md](adr/004-logging-module.md) - Logging module design

## Operational Runbooks

- [linting_failures.md](runbooks/linting_failures.md) - Troubleshooting linting failures
- [logging_issues.md](runbooks/logging_issues.md) - Resolving logging issues
- [validation_failures.md](runbooks/validation_failures.md) - Addressing validation failures

## Module Documentation

- [zcp_lint/README.md](../src/zcp_lint/README.md) - Linting module documentation
- [zcp_logging/README.md](../src/zcp_logging/README.md) - Logging module documentation
- [zcp_validate/README.md](../src/zcp_validate/README.md) - Validation module documentation

## Reference Material

- [validation_queries.md](../nrql/validation_queries.md) - NRQL queries for validation

## Component Structure

```
zcp/
├── zcp_core/        # Core utilities and event bus
├── zcp_preset/      # Preset loading and management
├── zcp_template/    # Template rendering with Jinja2
├── zcp_cost/        # Cost estimation with plugin architecture
├── zcp_rollout/     # Deployment orchestration
├── zcp_validate/    # Validation and verification
├── zcp_lint/        # Configuration linting
├── zcp_logging/     # Structured logging
└── zcp_cli/         # Command-line interface
```

## Recent Improvements

The latest version includes several critical fixes:

1. Data-model/Schema compatibility
   - Fixed snake_case vs camelCase inconsistencies
   - Implemented proper model alias handling

2. Event bus improvements
   - Fixed async task handling
   - Added exception handling for queues
   - Implemented unsubscribe functionality

3. CircuitBreaker logic fix
   - Fixed reset behavior in NRDB client

4. Python 3.11+ compatibility
   - Updated event loop creation
   - Fixed asyncio deprecation issues

5. Pydantic v1/v2 compatibility
   - Created compatibility layer
   - Updated dependencies

6. Resource loading and packaging
   - Improved resource discovery
   - Fixed wheel packaging

For full details, see [FIXES.md](../FIXES.md).
