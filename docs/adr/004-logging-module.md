# ADR 004: Logging Module Design

## Status

Accepted

## Context

The ZCP system needs a consistent logging approach across all components to enable troubleshooting, monitoring, and observability. This includes structured logging for machine parsing and OpenTelemetry support for distributed tracing.

## Decision

We will implement a logging module with the following characteristics:

1. A factory-based approach for creating consistently configured loggers
2. Support for both traditional text logging and structured JSON format
3. Context binding for adding metadata to log entries
4. Integration with OpenTelemetry for distributed tracing
5. Support for logging spans with timing information
6. Integration with event bus for critical errors
7. CLI commands for managing and testing logging

The logger implementation will follow a structured design with three key components:
- LoggerFactory: Central configuration point for all loggers
- JsonFormatter: JSON-based formatter for structured logging
- BoundLogger: Logger implementation with context binding and span support

## Consequences

### Positive

- Consistent logging across all components
- Structured data for easier parsing and analysis
- Context binding for better troubleshooting
- OpenTelemetry integration for distributed tracing
- CLI commands for easy configuration

### Negative

- Adds OpenTelemetry dependency (optional)
- Slightly more complex than standard Python logging
- May add performance overhead for highly verbose logging

## Reviewers

- ☑ SRE
- ☑ FinOps
- ☑ Sec-ops
