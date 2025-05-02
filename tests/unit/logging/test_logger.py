"""
Unit tests for the logger module.
"""

import json
import logging
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from zcp_logging.logger import BoundLogger, JsonFormatter, LoggerFactory


class TestLoggerFactory:
    """Tests for the LoggerFactory class."""
    
    def test_init_default(self):
        """Test default initialization."""
        with patch("zcp_logging.logger.logging") as mock_logging:
            # Reset initialized state
            LoggerFactory._initialized = False
            LoggerFactory._handlers = []
            
            # Initialize
            LoggerFactory.init()
            
            # Verify
            mock_logging.getLogger.assert_called()
            mock_logging.StreamHandler.assert_called()
            mock_logging.Formatter.assert_called()
    
    def test_init_json_format(self):
        """Test initialization with JSON format."""
        with patch("zcp_logging.logger.logging") as mock_logging:
            # Reset initialized state
            LoggerFactory._initialized = False
            LoggerFactory._handlers = []
            
            # Initialize with JSON format
            LoggerFactory.init(json_format=True)
            
            # Verify
            mock_logging.getLogger.assert_called()
            mock_logging.StreamHandler.assert_called()
    
    def test_get_logger(self):
        """Test getting a logger."""
        # Reset initialized state
        LoggerFactory._initialized = False
        LoggerFactory._handlers = []
        
        # Initialize and get logger
        with patch("zcp_logging.logger.logging"):
            logger = LoggerFactory.get("test")
            
            # Verify
            assert isinstance(logger, BoundLogger)
            assert logger._name == "test"


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""
    
    def test_format_basic(self):
        """Test basic JSON formatting."""
        formatter = JsonFormatter()
        
        # Create a record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        result = formatter.format(record)
        
        # Parse and verify
        log_data = json.loads(result)
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"
    
    def test_format_with_context(self):
        """Test JSON formatting with context."""
        formatter = JsonFormatter()
        
        # Create a record with context
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"user_id": 123, "request_id": "abc123"}
        
        # Format the record
        result = formatter.format(record)
        
        # Parse and verify
        log_data = json.loads(result)
        assert log_data["context"]["user_id"] == 123
        assert log_data["context"]["request_id"] == "abc123"


class TestBoundLogger:
    """Tests for the BoundLogger class."""
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        # Mock the underlying logger
        mock_logger = MagicMock()
        
        # Create bound logger
        logger = BoundLogger("test")
        logger._logger = mock_logger
        
        # Log a message
        logger.info("Test message")
        
        # Verify
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == logging.INFO
        assert args[1] == "Test message"
        
    def test_context_binding(self):
        """Test context binding."""
        # Create bound logger with context
        logger = BoundLogger("test", {"app": "zcp"})
        
        # Bind additional context
        new_logger = logger.bind(user="test_user")
        
        # Verify
        assert new_logger._context == {"app": "zcp", "user": "test_user"}
        assert logger._context == {"app": "zcp"}  # Original unchanged
    
    def test_span_logging(self):
        """Test span logging."""
        # Mock the underlying logger
        mock_logger = MagicMock()
        
        # Create bound logger
        logger = BoundLogger("test")
        logger._logger = mock_logger
        
        # Use span
        with logger.span("test_span", {"operation": "test"}):
            pass
        
        # Verify entry and exit logs
        assert mock_logger.debug.call_count >= 2
