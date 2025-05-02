"""
Unit tests for the validator module.
"""

from unittest.mock import MagicMock, patch

import pytest

from zcp_validate.models import ValidationJob, ValidationResult
from zcp_validate.validator import Validator


class TestValidator:
    """
    Tests for the Validator class.
    """
    
    def test_validate_success(self):
        """Test successful validation."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 12.0},
                {"hostname": "host2.example.com", "giBIngested": 10.0}
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.2,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish") as mock_publish:
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is True  # Both hosts within threshold
            assert len(result.host_results) == 2
            assert "host1.example.com" in result.host_results
            assert "host2.example.com" in result.host_results
            
            # host1 is within threshold (20% allowed deviation)
            assert result.host_results["host1.example.com"].actual_gib_day == 12.0
            assert result.host_results["host1.example.com"].within_threshold is True
            
            # host2 matches exactly
            assert result.host_results["host2.example.com"].actual_gib_day == 10.0
            assert result.host_results["host2.example.com"].within_threshold is True
            
            # Verify event was published
            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            assert event.topic == "validate.result"
            assert event.payload["pass"] is True
            assert event.payload["actual_gib_day"] == 11.0  # Average of 12.0 and 10.0
    
    def test_validate_failure(self):
        """Test validation with hosts outside threshold."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 15.0},  # 50% higher
                {"hostname": "host2.example.com", "giBIngested": 10.0}   # Exact match
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job with tight threshold
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.1,  # Only 10% deviation allowed
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish") as mock_publish:
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is False  # host1 outside threshold
            assert len(result.host_results) == 2
            
            # host1 is outside threshold (50% deviation, only 10% allowed)
            assert result.host_results["host1.example.com"].actual_gib_day == 15.0
            assert result.host_results["host1.example.com"].within_threshold is False
            assert result.host_results["host1.example.com"].deviation_percent == 50.0
            
            # host2 is within threshold
            assert result.host_results["host2.example.com"].actual_gib_day == 10.0
            assert result.host_results["host2.example.com"].within_threshold is True
            
            # Verify event was published
            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            assert event.topic == "validate.result"
            assert event.payload["pass"] is False
    
    def test_validate_nrdb_error(self):
        """Test validation when NRDB query fails."""
        # Mock NRDB client that raises an exception
        mock_client = MagicMock()
        mock_client.query.side_effect = RuntimeError("NRDB connection error")
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.1,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish") as mock_publish:
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is False
            assert len(result.host_results) == 2
            
            # All hosts should have error message
            for host, host_result in result.host_results.items():
                assert host_result.within_threshold is False
                assert host_result.actual_gib_day == 0.0
                assert "Error querying NRDB" in host_result.message
