"""
Unit tests for the rollout orchestrator.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from zcp_rollout.backends import PrintBackend
from zcp_rollout.models import HostResult, RolloutHost, RolloutJob
from zcp_rollout.orchestrator import RolloutOrchestrator


class TestRolloutOrchestrator:
    """
    Tests for the RolloutOrchestrator class.
    """
    
    def test_get_backend(self):
        """Test backend selection."""
        orchestrator = RolloutOrchestrator()
        
        # Test SSH backend
        backend = orchestrator._get_backend("ssh")
        assert backend.__class__.__name__ == "SSHBackend"
        
        # Test Ansible backend
        backend = orchestrator._get_backend("ansible")
        assert backend.__class__.__name__ == "AnsibleBackend"
        
        # Test Print backend
        backend = orchestrator._get_backend("print")
        assert backend.__class__.__name__ == "PrintBackend"
        
        # Test invalid backend
        with pytest.raises(ValueError):
            orchestrator._get_backend("invalid")
            
    def test_process_host_success(self):
        """Test successful host processing."""
        # Create mock backend
        mock_backend = MagicMock()
        mock_backend.transfer.return_value = HostResult(
            hostname="test.example.com",
            success=True,
            message="Transfer success",
            duration_ms=100
        )
        mock_backend.restart.return_value = HostResult(
            hostname="test.example.com",
            success=True,
            message="Restart success",
            duration_ms=200
        )
        
        # Create orchestrator and test
        orchestrator = RolloutOrchestrator(backend=mock_backend)
        host = RolloutHost(hostname="test.example.com")
        result = orchestrator._process_host(
            host=host,
            content="test content",
            filename="test.yaml",
            backend=mock_backend
        )
        
        # Verify
        assert result.success is True
        assert result.message == "Restart success"
        assert result.duration_ms == 200
        mock_backend.transfer.assert_called_once()
        mock_backend.restart.assert_called_once()
        
    def test_process_host_transfer_failure(self):
        """Test host processing with transfer failure."""
        # Create mock backend
        mock_backend = MagicMock()
        mock_backend.transfer.return_value = HostResult(
            hostname="test.example.com",
            success=False,
            message="Transfer failed",
            duration_ms=100
        )
        
        # Create orchestrator and test
        orchestrator = RolloutOrchestrator(backend=mock_backend)
        host = RolloutHost(hostname="test.example.com")
        result = orchestrator._process_host(
            host=host,
            content="test content",
            filename="test.yaml",
            backend=mock_backend
        )
        
        # Verify
        assert result.success is False
        assert result.message == "Transfer failed"
        assert result.duration_ms == 100
        mock_backend.transfer.assert_called_once()
        mock_backend.restart.assert_not_called()  # Restart should not be called on transfer failure
        
    @patch("zcp_rollout.orchestrator.concurrent.futures.ThreadPoolExecutor")
    @patch("zcp_rollout.orchestrator.publish")
    def test_execute(self, mock_publish, mock_executor):
        """Test job execution."""
        # Set up mock executor
        mock_future = MagicMock()
        mock_future.result.return_value = HostResult(
            hostname="test.example.com",
            success=True,
            message="Success",
            duration_ms=300
        )
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        # Create job
        job = RolloutJob(
            hosts=[RolloutHost(hostname="test.example.com")],
            config_content="test content",
            config_filename="test.yaml",
            checksum="test_checksum",
            parallel=10
        )
        
        # Execute
        orchestrator = RolloutOrchestrator()
        report = orchestrator.execute(job, mode="print")
        
        # Verify
        assert report.success == 1
        assert report.fail == 0
        assert "test.example.com" in report.results
        assert report.results["test.example.com"].success is True
        mock_publish.assert_called_once()
        mock_executor.assert_called_once_with(max_workers=10)
