# ZCP Logging Module

The logging module provides structured logging and OpenTelemetry integration for the ZCP system.

## Features

- **Centralized Configuration**: Common configuration for all loggers
- **Structured Logging**: Support for both text and JSON formats
- **Context Binding**: Add metadata to log entries
- **OpenTelemetry Integration**: Support for distributed tracing
- **Span Support**: Create and track logical operations with timing
- **Event Bus Integration**: Publish critical errors to the event bus
- **CLI Integration**: Commands for managing and testing logging

## Usage

### CLI Examples

```bash
# Initialize logging with custom settings
zcp logging init --level DEBUG --json --otlp --otlp-endpoint http://otel-collector:4317

# Test logging at different levels
zcp logging test --level WARNING
```

### Basic Logging

```python
from zcp_logging.logger import LoggerFactory

# Get a logger
logger = LoggerFactory.get("my_component")

# Log at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Structured Logging with Context

```python
from zcp_logging.logger import LoggerFactory

# Get a logger
logger = LoggerFactory.get("my_component")

# Add context to all logs from this logger
user_logger = logger.bind(user_id="user123", session_id="abc456")

# Log with context
user_logger.info("User logged in")

# Add additional context to a specific log
user_logger.info("User performed action", context={"action": "download", "file_id": "file123"})
```

### Using Spans

```python
from zcp_logging.logger import LoggerFactory

# Get a logger
logger = LoggerFactory.get("my_component")

# Create a span for a logical operation
with logger.span("process_file", context={"file_id": "file123"}):
    # Do some work
    logger.info("Processing file")
    # More work
    logger.info("File processed")
```

## OpenTelemetry Integration

When OpenTelemetry is enabled, spans are created using the OpenTelemetry SDK and exported via OTLP. This allows for distributed tracing across multiple services.

### Requirements

To use OpenTelemetry integration, install the required packages:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

### Configuration

The OpenTelemetry endpoint can be configured via:

1. Environment variable:
   ```bash
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
   ```

2. CLI parameter:
   ```bash
   zcp logging init --otlp --otlp-endpoint http://otel-collector:4317
   ```

## JSON Logging

When JSON logging is enabled, log entries are formatted as JSON objects with the following structure:

```json
{
  "timestamp": "2023-05-02T14:30:00.123456",
  "level": "INFO",
  "logger": "my_component",
  "message": "User logged in",
  "thread": "MainThread",
  "process": "MainProcess",
  "context": {
    "user_id": "user123",
    "session_id": "abc456"
  }
}
```

## Testing

The module includes unit tests for all components:

```bash
pytest tests/unit/logging/
```
