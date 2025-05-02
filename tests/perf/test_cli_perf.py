"""Performance benchmarks for the CLI and cost model."""

import pytest
import tempfile
from process_lab.cost.static import estimate_cost, estimate_gb_day
from typer.testing import CliRunner
from process_lab.cli import app


@pytest.mark.benchmark
def test_static_cost_model_perf(benchmark):
    """Benchmark the static cost model performance."""
    def run_static_model():
        for rate in [20, 60, 120, 300]:
            for keep in [0.1, 0.5, 1.0]:
                for proc in [50, 150, 500]:
                    estimate_gb_day(
                        sample_rate=rate,
                        keep_ratio=keep,
                        process_count=proc
                    )
    
    # Run the benchmark
    result = benchmark(run_static_model)
    
    # Ensure the benchmark completes within budget
    assert result.stats.stats.mean < 0.01  # 10ms max average time


@pytest.mark.benchmark
def test_cost_estimate_perf(benchmark):
    """Benchmark the full cost estimation performance."""
    def run_full_estimate():
        for rate in [20, 60, 120, 300]:
            for keep in [0.1, 0.5, 1.0]:
                for proc in [50, 150, 500]:
                    estimate_cost(
                        sample_rate=rate,
                        keep_ratio=keep,
                        process_count=proc,
                        avg_bytes=450.0,
                        price_per_gb=0.35
                    )
    
    # Run the benchmark
    result = benchmark(run_full_estimate)
    
    # Ensure the benchmark completes within budget
    assert result.stats.stats.mean < 0.02  # 20ms max average time


@pytest.mark.benchmark
def test_cli_help_perf(benchmark):
    """Benchmark the CLI help command performance."""
    runner = CliRunner()
    
    def run_cli_help():
        runner.invoke(app, ["--help"])
    
    # Run the benchmark
    result = benchmark(run_cli_help)
    
    # Ensure the benchmark completes within budget
    assert result.stats.stats.mean < 0.1  # 100ms max average time


@pytest.mark.benchmark
def test_cli_estimate_cost_perf(benchmark):
    """Benchmark the CLI estimate-cost command performance."""
    runner = CliRunner()
    
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix='.yml') as temp:
        temp.write(b"""
metrics_process_sample_rate: 60
exclude_matching_metrics:
  process.chrome.*: true
  process.firefox.*: true
        """)
        temp.flush()
        
        def run_estimate_cost():
            runner.invoke(app, [
                "estimate-cost",
                "--yaml", temp.name,
                "--price-per-gb", "0.35",
            ])
        
        # Run the benchmark
        result = benchmark(run_estimate_cost)
        
        # Ensure the benchmark completes within budget
        # Note: This is higher since it would involve real CLI startup
        assert result.stats.stats.mean < 0.5  # 500ms max average time
