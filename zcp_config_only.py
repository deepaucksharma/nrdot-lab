#!/usr/bin/env python
"""
Entry point for the configuration-only ZCP CLI.

This script provides a convenient way to run the simplified ZCP CLI
that focuses only on configuration generation and cost estimation,
with no linting, rollout, or validation functionality.
"""

import sys
from src.zcp_cli.config_only_cli import cli

if __name__ == "__main__":
    cli()
