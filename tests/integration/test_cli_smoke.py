"""Smoke tests for the CLI interface."""

import pytest
from typer.testing import CliRunner
from process_lab.cli import app

# Initialize CLI test runner
runner = CliRunner()


def test_cli_help():
    """Test the CLI help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "process-lab" in result.stdout
    assert "A toolkit for optimizing" in result.stdout
    
    # Check that all commands are listed
    assert "wizard" in result.stdout
    assert "generate-configs" in result.stdout
    assert "estimate-cost" in result.stdout
    assert "validate" in result.stdout
    assert "lint" in result.stdout
    assert "rollout" in result.stdout
    assert "nrdb" in result.stdout


def test_cli_version():
    """Test the CLI version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "process-lab" in result.stdout


@pytest.mark.parametrize("command", [
    "wizard",
    "generate-configs",
    "estimate-cost",
    "validate",
    "lint",
    "rollout",
    "nrdb",
])
def test_command_help(command):
    """Test help text for each command."""
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0
    assert command in result.stdout


def test_estimate_cost_cli():
    """Test the estimate-cost command."""
    result = runner.invoke(app, [
        "estimate-cost",
        "--price-per-gb", "0.5",
        "--window", "6h"
    ])
    assert result.exit_code == 1  # Currently exits with error since not implemented
    assert "Est:" in result.stdout
    assert "GB/day" in result.stdout


def test_generate_configs_cli():
    """Test the generate-configs command."""
    result = runner.invoke(app, [
        "generate-configs",
        "--sample-rate", "90",
        "--filter-type", "aggressive",
        "--template", "web_standard"
    ])
    assert result.exit_code == 1  # Currently exits with error since not implemented
    assert "rate=90" in result.stdout
    assert "filter=aggressive" in result.stdout
    assert "template=web_standard" in result.stdout


def test_rollout_cli():
    """Test the rollout command."""
    result = runner.invoke(app, [
        "rollout",
        "--mode", "ssh",
        "--hosts", "server1,server2",
        "--force"
    ])
    assert result.exit_code == 1  # Currently exits with error since not implemented
    assert "mode=ssh" in result.stdout
    assert "hosts=server1,server2" in result.stdout
    assert "force=True" in result.stdout
