#!/usr/bin/env python
"""
Entry point for the streamlined ZCP CLI.

This script provides a convenient way to run the simplified ZCP CLI
without having to use the module import syntax.
"""

import sys
from src.zcp_cli.simple_cli import cli

if __name__ == "__main__":
    cli()
