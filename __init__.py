"""
Process-Lab: New Relic Infrastructure Agent Configuration Toolkit

A comprehensive toolkit enabling SREs to discover, predict, generate, validate,
and roll out cost-optimized ProcessSample configurations using the New Relic
Infrastructure Agent and NRDB analysis.
"""

__version__ = "0.1.7"

# Main classes
from .main import ProcessLab

# Core functionality
from .core import config
from .core import cost
from .core import analysis

# Utilities
from .utils import lint
from .utils import rollout

# Client
from .client import NRDBClient

# CLI
from .cli import app

__all__ = [
    "ProcessLab",
    "config",
    "cost",
    "analysis",
    "lint",
    "rollout",
    "NRDBClient",
    "app",
]
