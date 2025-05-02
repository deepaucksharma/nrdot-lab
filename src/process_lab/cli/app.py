"""
Command Line Interface for Process-Lab.

This module defines the main CLI entry point and command structure.
"""

import os
import sys
from typing import Optional, List
from pathlib import Path

import typer
from rich.console import Console

from .commands import (
    wizard_command,
    generate_config_command,
    list_presets_command,
    list_filters_command,
    estimate_cost_command,
    validate_command,
    lint_command,
    rollout_command,
    visualize_command,
    recommend_command,
    nrdb_command,
)

# Create the main CLI application
app = typer.Typer(
    name="process-lab",
    help="A toolkit for optimizing New Relic Infrastructure Agent ProcessSample configurations",
    add_completion=False,
)

# Create the console for rich output
console = Console()


@app.callback()
def callback() -> None:
    """
    ProcessSample Configuration Toolkit

    Helps SREs discover, predict, generate, validate, and roll out cost-optimized
    ProcessSample configurations using the New Relic Infrastructure Agent.
    """
    pass


# Register commands
app.command(name="wizard")(wizard_command)
app.command(name="generate-config")(generate_config_command)
app.command(name="list-presets")(list_presets_command)
app.command(name="list-filters")(list_filters_command)
app.command(name="estimate-cost")(estimate_cost_command)
app.command(name="validate")(validate_command)
app.command(name="lint")(lint_command)
app.command(name="rollout")(rollout_command)
app.command(name="visualize")(visualize_command)
app.command(name="recommend")(recommend_command)
app.command(name="nrdb")(nrdb_command)


if __name__ == "__main__":
    app()
