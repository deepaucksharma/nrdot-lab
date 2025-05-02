"""
Extended unit tests for the validator module.

These tests cover more complex validation scenarios including:
1. Partial host data availability
2. Threshold edge cases
3. Confidence level adjustments
4. Timeframe variations
5. Large host sets
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from zcp_validate.models import ValidationJob, ValidationResult
from zcp_validate.validator import Validator


class TestValidatorComplex:
    """
    Advanced tests for the Validator class.
    """
    
    def test_partial_host_data_availability(self):
        """Test validation when data is only available for some hosts."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 12.0},
                # host2 is missing from results
                {"hostname": "host3.example.com", "giBIngested": 8.0}
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job with hosts including one that won't have data
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com", "host3.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.2,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish"):
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is False  # Missing host causes failure
            assert len(result.host_results) == 3
            
            # host1 is within threshold
            assert result.host_results["host1.example.com"].actual_gib_day == 12.0
            assert result.host_results["host1.example.com"].within_threshold is True
            
            # host2 should be marked as missing data
            assert result.host_results["host2.example.com"].actual_gib_day == 0.0
            assert result.host_results["host2.example.com"].within_threshold is False
            assert "No data found" in result.host_results["host2.example.com"].message
            
            # host3 is within threshold
            assert result.host_results["host3.example.com"].actual_gib_day == 8.0
            assert result.host_results["host3.example.com"].within_threshold is True
    
    def test_threshold_edge_cases(self):
        """Test validation with values exactly at threshold limits."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                # Exactly at lower threshold (8.0 = 10.0 - 20%)
                {"hostname": "host1.example.com", "giBIngested": 8.0},
                # Exactly at upper threshold (12.0 = 10.0 + 20%)
                {"hostname": "host2.example.com", "giBIngested": 12.0},
                # Slightly beyond lower threshold (7.9 < 8.0)
                {"hostname": "host3.example.com", "giBIngested": 7.9},
                # Slightly beyond upper threshold (12.1 > 12.0)
                {"hostname": "host4.example.com", "giBIngested": 12.1}
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job with 20% threshold
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com", "host3.example.com", "host4.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.2,  # 20% deviation allowed
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish"):
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is False  # Two hosts outside threshold
            
            # host1: exactly at lower threshold - should pass
            assert result.host_results["host1.example.com"].actual_gib_day == 8.0
            assert result.host_results["host1.example.com"].deviation_percent == -20.0
            assert result.host_results["host1.example.com"].within_threshold is True
            
            # host2: exactly at upper threshold - should pass
            assert result.host_results["host2.example.com"].actual_gib_day == 12.0
            assert result.host_results["host2.example.com"].deviation_percent == 20.0
            assert result.host_results["host2.example.com"].within_threshold is True
            
            # host3: just beyond lower threshold - should fail
            assert result.host_results["host3.example.com"].actual_gib_day == 7.9
            assert round(result.host_results["host3.example.com"].deviation_percent, 1) == -21.0
            assert result.host_results["host3.example.com"].within_threshold is False
            
            # host4: just beyond upper threshold - should fail
            assert result.host_results["host4.example.com"].actual_gib_day == 12.1
            assert round(result.host_results["host4.example.com"].deviation_percent, 1) == 21.0
            assert result.host_results["host4.example.com"].within_threshold is False
    
    def test_confidence_adjusts_threshold(self):
        """Test that confidence level adjusts threshold appropriately."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 13.0},  # 30% higher
                {"hostname": "host2.example.com", "giBIngested": 7.0},   # 30% lower
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Different confidence levels with same base threshold
        confidence_levels = [
            (1.0, False),  # Perfect confidence - threshold stays at 20%
            (0.8, False),  # Good confidence - threshold stays close to 20%
            (0.5, True),   # Medium confidence - threshold expands enough to pass
            (0.2, True)    # Low confidence - threshold expands significantly
        ]
        
        for confidence, expected_pass in confidence_levels:
            # Create job with specified confidence
            job = ValidationJob(
                hosts=["host1.example.com", "host2.example.com"],
                expected_gib_day=10.0,
                confidence=confidence,
                threshold=0.2,  # Base threshold is 20%
                timeframe_hours=24
            )
            
            # Execute validation
            with patch("zcp_validate.validator.publish"):
                result = validator.validate(job)
                
                # Verify result matches expected pass/fail based on confidence
                assert result.overall_pass is expected_pass, f"Failed for confidence {confidence}"
                
                # For debugging, print the adjusted thresholds
                if not expected_pass:
                    assert any(not hr.within_threshold for hr in result.host_results.values())
                else:
                    assert all(hr.within_threshold for hr in result.host_results.values())
    
    def test_different_timeframes(self):
        """Test validation with different timeframe settings."""
        # Create a validator that captures the timeframe parameter
        class TimeframeCapturingValidator(Validator):
            def __init__(self, nrdb_client):
                super().__init__(nrdb_client)
                self.last_timeframe = None
            
            def _query_actual_ingest(self, hosts, timeframe_hours):
                self.last_timeframe = timeframe_hours
                return super()._query_actual_ingest(hosts, timeframe_hours)
        
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 12.0}
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = TimeframeCapturingValidator(nrdb_client=mock_client)
        
        # Test different timeframes
        timeframes = [1, 24, 48, 168]  # hours
        
        for timeframe in timeframes:
            # Create job with specified timeframe
            job = ValidationJob(
                hosts=["host1.example.com"],
                expected_gib_day=10.0,
                confidence=0.8,
                threshold=0.2,
                timeframe_hours=timeframe
            )
            
            # Execute validation
            with patch("zcp_validate.validator.publish"):
                validator.validate(job)
                
                # Verify timeframe was passed correctly
                assert validator.last_timeframe == timeframe
                
                # Verify NRDB was queried with correct timeframe
                mock_client.query.assert_called()
                query_text = mock_client.query.call_args[0][0]
                assert f"SINCE {timeframe} HOURS AGO" in query_text
    
    def test_large_host_set(self):
        """Test validation with a large number of hosts."""
        # Number of hosts to test
        host_count = 1000
        
        # Generate host list
        hosts = [f"host{i}.example.com" for i in range(host_count)]
        
        # Generate results with 90% of hosts exactly matching expected
        # and 10% being outside threshold
        results = []
        for i in range(host_count):
            if i < host_count * 0.9:
                # Within threshold
                results.append({"hostname": f"host{i}.example.com", "giBIngested": 10.0})
            else:
                # Outside threshold
                results.append({"hostname": f"host{i}.example.com", "giBIngested": 15.0})
        
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": results,
            "duration_ms": 1500.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job
        job = ValidationJob(
            hosts=hosts,
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.2,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish"):
            start_time = __import__('time').time()
            result = validator.validate(job)
            end_time = __import__('time').time()
            
            # Verify performance is reasonable
            assert end_time - start_time < 2.0, "Validation took too long"
            
            # Verify results
            assert result.overall_pass is False
            assert len(result.host_results) == host_count
            
            # 90% should be within threshold
            passing_hosts = sum(1 for hr in result.host_results.values() if hr.within_threshold)
            assert passing_hosts == int(host_count * 0.9)
    
    def test_zero_expected_gib(self):
        """Test validation when expected GiB is zero."""
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 0.0},  # Exact match
                {"hostname": "host2.example.com", "giBIngested": 0.1}   # Small amount
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = Validator(nrdb_client=mock_client)
        
        # Create job with zero expected GiB
        job = ValidationJob(
            hosts=["host1.example.com", "host2.example.com"],
            expected_gib_day=0.0,
            confidence=0.8,
            threshold=0.2,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish"):
            result = validator.validate(job)
            
            # Verify result
            assert result.overall_pass is False  # One host with non-zero value
            
            # host1 exact match should pass
            assert result.host_results["host1.example.com"].actual_gib_day == 0.0
            assert result.host_results["host1.example.com"].within_threshold is True
            
            # host2 should fail - with zero expected, any value is outside threshold
            assert result.host_results["host2.example.com"].actual_gib_day == 0.1
            assert result.host_results["host2.example.com"].within_threshold is False
    
    def test_validation_with_custom_nrql(self):
        """Test validation with a custom NRQL query template."""
        # Create a validator with custom query template
        class CustomQueryValidator(Validator):
            def __init__(self, nrdb_client):
                super().__init__(nrdb_client)
                self.query_template = """
                SELECT hostname, sum(bytesIngested)/1073741824 as giBIngested 
                FROM ProcessSample 
                WHERE hostname IN ({hosts})
                FACET hostname 
                SINCE {timeframe} HOURS AGO
                """
        
        # Mock NRDB client
        mock_client = MagicMock()
        mock_client.query.return_value = {
            "results": [
                {"hostname": "host1.example.com", "giBIngested": 12.0}
            ],
            "duration_ms": 150.0
        }
        
        # Create validator with mock client
        validator = CustomQueryValidator(nrdb_client=mock_client)
        
        # Create job
        job = ValidationJob(
            hosts=["host1.example.com"],
            expected_gib_day=10.0,
            confidence=0.8,
            threshold=0.2,
            timeframe_hours=24
        )
        
        # Execute validation
        with patch("zcp_validate.validator.publish"):
            validator.validate(job)
            
            # Verify custom query was used
            mock_client.query.assert_called_once()
            query_text = mock_client.query.call_args[0][0]
            assert "FROM ProcessSample" in query_text
            assert "sum(bytesIngested)/1073741824" in query_text
