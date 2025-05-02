"""
Logger implementation with structured logging and OTLP support.
"""

import json
import logging
import os
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Union

from zcp_core.bus import Event, publish


class LoggerFactory:
    """
    Factory for creating loggers with consistent configuration.
    
    Supports both standard Python logging and OpenTelemetry (OTLP) spans.
    """
    
    _initialized = False
    _handlers = []
    _otlp_enabled = False
    
    @classmethod
    def init(cls, 
             level: str = "INFO", 
             enable_otlp: bool = False,
             json_format: bool = False) -> None:
        """
        Initialize logging system.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_otlp: Whether to enable OpenTelemetry
            json_format: Whether to use JSON format for logs
        """
        if cls._initialized:
            return
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level))
        
        # Remove existing handlers
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        cls._handlers.append(console_handler)
        
        # Initialize OpenTelemetry if requested
        cls._otlp_enabled = enable_otlp
        if enable_otlp:
            try:
                cls._init_otlp()
            except ImportError:
                logging.warning("OpenTelemetry libraries not installed, OTLP logging disabled")
                cls._otlp_enabled = False
        
        cls._initialized = True
        
        # Log initialization
        logging.info("Logging initialized with level=%s, otlp=%s, json=%s", 
                    level, enable_otlp, json_format)
    
    @classmethod
    def _init_otlp(cls) -> None:
        """
        Initialize OpenTelemetry for tracing.
        
        Raises:
            ImportError: If OpenTelemetry libraries are not installed
        """
        try:
            # Import OpenTelemetry modules
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            
            # Create tracer provider
            resource = Resource(attributes={
                "service.name": "zcp",
                "service.version": os.environ.get("ZCP_VERSION", "0.1.0")
            })
            
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Create OTLP exporter
            otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            logging.info("OpenTelemetry initialized with endpoint: %s", otlp_endpoint)
        except ImportError as e:
            raise ImportError(f"OpenTelemetry libraries not installed: {e}") from e
    
    @classmethod
    def get(cls, name: str) -> 'BoundLogger':
        """
        Get a logger for the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            BoundLogger instance
        """
        if not cls._initialized:
            cls.init()
        
        return BoundLogger(name)


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON-formatted log entry
        """
        log_object = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "thread": record.threadName,
            "process": record.processName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add context if present
        if hasattr(record, "context") and record.context:
            log_object["context"] = record.context
        
        return json.dumps(log_object)


class BoundLogger:
    """
    Logger with context binding and OpenTelemetry integration.
    """
    
    def __init__(self, name: str, context: Dict[str, Any] = None):
        """
        Initialize bound logger.
        
        Args:
            name: Logger name
            context: Context to bind to logger
        """
        self._logger = logging.getLogger(name)
        self._context = context or {}
        self._name = name
    
    def bind(self, **kwargs) -> 'BoundLogger':
        """
        Create a new logger with additional context.
        
        Args:
            **kwargs: Context to add
            
        Returns:
            New BoundLogger with combined context
        """
        new_context = self._context.copy()
        new_context.update(kwargs)
        return BoundLogger(self._name, new_context)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """
        Log a debug message.
        
        Args:
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """
        Log an info message.
        
        Args:
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """
        Log a warning message.
        
        Args:
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """
        Log an error message.
        
        Args:
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """
        Log a critical message.
        
        Args:
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def _log(self, level: int, msg: str, *args, **kwargs) -> None:
        """
        Internal logging implementation.
        
        Args:
            level: Logging level
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional context or logging parameters
        """
        # Extract context and extra
        context = kwargs.pop("context", {})
        extra = kwargs.pop("extra", {})
        
        # Combine context
        combined_context = self._context.copy()
        combined_context.update(context)
        
        # Add context to extra
        extra["context"] = combined_context
        
        # Log the message
        self._logger.log(level, msg, *args, extra=extra, **kwargs)
        
        # Publish event for critical or error logs
        if level >= logging.ERROR:
            publish(Event(
                topic="logging.error",
                payload={
                    "level": logging.getLevelName(level),
                    "message": msg % args if args else msg,
                    "context": combined_context
                }
            ))
    
    @contextmanager
    def span(self, name: str, context: Dict[str, Any] = None) -> Iterator[None]:
        """
        Create a logging span.
        
        In OTLP mode, creates an OpenTelemetry span.
        In standard mode, logs entry and exit.
        
        Args:
            name: Span name
            context: Additional context for span
            
        Yields:
            None
        """
        combined_context = self._context.copy()
        if context:
            combined_context.update(context)
        
        if LoggerFactory._otlp_enabled:
            try:
                from opentelemetry import trace
                tracer = trace.get_tracer(self._name)
                with tracer.start_as_current_span(name, attributes=combined_context) as span:
                    yield span
            except (ImportError, Exception) as e:
                self._logger.warning("Failed to create OTLP span: %s", str(e))
                self._logger.debug("Entering span: %s", name, extra={"context": combined_context})
                start_time = time.time()
                try:
                    yield None
                finally:
                    elapsed_ms = (time.time() - start_time) * 1000
                    self._logger.debug("Exiting span: %s (elapsed: %.2f ms)", 
                                      name, elapsed_ms, extra={"context": combined_context})
        else:
            self._logger.debug("Entering span: %s", name, extra={"context": combined_context})
            start_time = time.time()
            try:
                yield None
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                self._logger.debug("Exiting span: %s (elapsed: %.2f ms)", 
                                  name, elapsed_ms, extra={"context": combined_context})
