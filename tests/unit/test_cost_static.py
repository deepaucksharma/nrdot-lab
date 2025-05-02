"""Unit tests for the static cost model."""

import pytest
from process_lab.cost.static import estimate_gb_day, estimate_cost


def test_estimate_gb_day_default_values():
    """Test estimate_gb_day with default values."""
    # Default: 150 processes, 450 bytes/event, 1.1 safety factor
    gb_day = estimate_gb_day(sample_rate=60, keep_ratio=1.0)
    
    # Expected calculation:
    # events_per_day = (86400 / 60) * 150 * 1.0 = 216000
    # gb_per_day = 216000 * 450 / 1e9 = 0.0972
    # with safety factor: 0.0972 * 1.1 = 0.10692
    expected = 0.10692
    
    assert abs(gb_day - expected) < 0.0001


def test_estimate_gb_day_custom_values():
    """Test estimate_gb_day with custom values."""
    gb_day = estimate_gb_day(
        sample_rate=30,
        keep_ratio=0.5,
        process_count=200,
        avg_bytes=500,
    )
    
    # Expected calculation:
    # events_per_day = (86400 / 30) * 200 * 0.5 = 288000
    # gb_per_day = 288000 * 500 / 1e9 = 0.144
    # with safety factor: 0.144 * 1.1 = 0.1584
    expected = 0.1584
    
    assert abs(gb_day - expected) < 0.0001


def test_estimate_gb_day_extreme_values():
    """Test estimate_gb_day with extreme values."""
    # Minimum sample rate
    min_rate = estimate_gb_day(sample_rate=20, keep_ratio=1.0, process_count=100)
    
    # Maximum sample rate
    max_rate = estimate_gb_day(sample_rate=300, keep_ratio=1.0, process_count=100)
    
    # Min rate should produce more events than max rate
    assert min_rate > max_rate
    
    # Zero keep ratio should result in zero GB
    zero_keep = estimate_gb_day(sample_rate=60, keep_ratio=0.0)
    assert zero_keep == 0.0


def test_estimate_cost_result_structure():
    """Test the structure of the estimate_cost result."""
    result = estimate_cost(sample_rate=60, keep_ratio=0.5)
    
    # Check that all expected keys are present
    assert "gb_day" in result
    assert "monthly_cost" in result
    assert "confidence" in result
    assert "method" in result
    assert "inputs" in result
    
    # Check input parameters are recorded
    assert result["inputs"]["sample_rate"] == 60
    assert result["inputs"]["keep_ratio"] == 0.5
    assert result["inputs"]["process_count"] == 150  # default
    assert result["inputs"]["avg_bytes"] == 450.0  # default
    assert result["inputs"]["price_per_gb"] == 0.35  # default
    
    # Check method is correct
    assert result["method"] == "static"
    
    # Check confidence is between 0 and 1
    assert 0 <= result["confidence"] <= 1


def test_estimate_cost_monthly_calculation():
    """Test the monthly cost calculation."""
    result = estimate_cost(
        sample_rate=60,
        keep_ratio=1.0,
        process_count=100,
        avg_bytes=500,
        price_per_gb=0.5,
    )
    
    # Calculate expected GB/day
    # events_per_day = (86400 / 60) * 100 * 1.0 = 144000
    # gb_per_day = 144000 * 500 / 1e9 = 0.072
    # with safety factor: 0.072 * 1.1 = 0.0792
    expected_gb_day = 0.0792
    
    # Calculate expected monthly cost
    expected_monthly = expected_gb_day * 30 * 0.5  # 30 days, $0.50/GB
    
    # Check calculated values
    assert abs(result["gb_day"] - expected_gb_day) < 0.0001
    assert abs(result["monthly_cost"] - expected_monthly) < 0.0001
