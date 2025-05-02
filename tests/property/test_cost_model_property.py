"""Property-based tests for the cost model."""

from hypothesis import given, strategies as st
import pytest
from process_lab.cost.static import estimate_gb_day, estimate_cost


@given(
    rate=st.integers(min_value=20, max_value=300),
    keep=st.floats(min_value=0.05, max_value=1.0),
    proc=st.integers(min_value=5, max_value=500)
)
def test_static_cost_safety(rate, keep, proc):
    """
    Test that the static cost model is never more than 10% optimistic.
    
    This property ensures our cost estimates are conservative and won't
    underestimate actual costs by more than 10%.
    """
    est = estimate_gb_day(rate, keep, proc)
    
    # Brute force calculation - 1.5 KB avg byte heuristic (higher than our default)
    brute = (86400 / rate) * proc * 1500 / 1e9 * keep
    
    # Our estimate should never be more than 10% optimistic
    assert est >= brute * 0.9


@given(
    rate=st.integers(min_value=20, max_value=300),
    keep=st.floats(min_value=0.0, max_value=1.0),
    proc=st.integers(min_value=1, max_value=1000),
    bytes_per_event=st.floats(min_value=100.0, max_value=2000.0),
    price=st.floats(min_value=0.1, max_value=1.0)
)
def test_cost_estimate_consistency(rate, keep, proc, bytes_per_event, price):
    """
    Test consistency between gb_day and monthly_cost in the estimate.
    
    This property ensures the relationship between GB/day and monthly cost
    is always maintained correctly.
    """
    result = estimate_cost(
        sample_rate=rate,
        keep_ratio=keep,
        process_count=proc,
        avg_bytes=bytes_per_event,
        price_per_gb=price
    )
    
    # Check that monthly_cost = gb_day * 30 * price_per_gb
    expected_monthly = result["gb_day"] * 30 * price
    assert abs(result["monthly_cost"] - expected_monthly) < 0.001


@given(
    rate1=st.integers(min_value=20, max_value=300),
    rate2=st.integers(min_value=20, max_value=300),
    keep=st.floats(min_value=0.1, max_value=1.0),
    proc=st.integers(min_value=10, max_value=500)
)
def test_sample_rate_inverse_relation(rate1, rate2, keep, proc):
    """
    Test that cost is inversely related to sample rate.
    
    This property ensures that increasing the sample rate (sampling less frequently)
    always reduces the cost estimate, all else being equal.
    """
    if rate1 == rate2:
        return  # Skip equal rates
        
    est1 = estimate_gb_day(rate1, keep, proc)
    est2 = estimate_gb_day(rate2, keep, proc)
    
    # If rate1 < rate2 (sampling more frequently), then est1 > est2
    if rate1 < rate2:
        assert est1 > est2
    else:
        assert est1 < est2


@given(
    rate=st.integers(min_value=20, max_value=300),
    keep1=st.floats(min_value=0.1, max_value=0.9),
    keep2=st.floats(min_value=0.1, max_value=0.9),
    proc=st.integers(min_value=10, max_value=500)
)
def test_keep_ratio_direct_relation(rate, keep1, keep2, proc):
    """
    Test that cost is directly related to keep_ratio.
    
    This property ensures that increasing the keep ratio (keeping more samples)
    always increases the cost estimate, all else being equal.
    """
    if abs(keep1 - keep2) < 0.01:
        return  # Skip nearly equal keep ratios
        
    est1 = estimate_gb_day(rate, keep1, proc)
    est2 = estimate_gb_day(rate, keep2, proc)
    
    # If keep1 < keep2 (keeping fewer samples), then est1 < est2
    if keep1 < keep2:
        assert est1 < est2
    else:
        assert est1 > est2


@given(
    rate=st.integers(min_value=20, max_value=300),
    keep=st.floats(min_value=0.0, max_value=1.0)
)
def test_zero_processes_zero_cost(rate, keep):
    """
    Test that zero processes results in zero cost.
    
    This property ensures that with zero processes, the cost is always zero,
    regardless of other parameters.
    """
    est = estimate_gb_day(rate, keep, 0)
    assert est == 0.0
