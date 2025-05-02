"""
Process-Lab main module.

This module provides the main ProcessLab class which serves as the
high-level interface for the toolkit.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .core import config
from .core import cost
from .core import analysis
from .utils import lint
from .utils import rollout
from .client.nrdb import NRDBClient


class ProcessLab:
    """Main class for Process-Lab toolkit."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the Process-Lab toolkit.
        
        Args:
            api_key: New Relic API key (defaults to environment variable)
            config_dir: Directory for configuration files
            output_dir: Directory for outputs (reports, artifacts, etc.)
        """
        self.api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        self.config_dir = config_dir or Path("./config")
        self.output_dir = output_dir or Path("./output")
        
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize NRDB client if API key is available
        self.nrdb_client = None
        if self.api_key:
            self.nrdb_client = NRDBClient(api_key=self.api_key)

    def generate_config(
        self,
        sample_rate: int = 60,
        filter_type: str = "standard",
        collect_cmdline: bool = False,
        log_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a configuration file.
        
        Args:
            sample_rate: Process sample rate in seconds
            filter_type: Filter type (standard, aggressive)
            collect_cmdline: Whether to collect command line arguments
            log_file: Log file path
            output_path: Output path for the configuration file
            
        Returns:
            Generated YAML configuration
        """
        # Set up overrides
        overrides = {"collect_command_line": collect_cmdline}
        if log_file:
            overrides["log_file"] = log_file
            
        # Generate configuration
        yaml_content = config.render_agent_yaml(
            sample_rate=sample_rate,
            filter_type=filter_type,
            overrides=overrides
        )
        
        # Write to file if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(yaml_content)
                
        return yaml_content

    def generate_from_preset(
        self,
        preset_name: str,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a configuration from a preset.
        
        Args:
            preset_name: Name of the preset
            output_path: Output path for the configuration file
            
        Returns:
            Generated YAML configuration
        """
        return config.generate_config_from_preset(preset_name, output_path)

    def estimate_cost(
        self,
        config_path: Path,
        price_per_gb: float = 0.35,
        window: str = "6h",
    ) -> Dict[str, Any]:
        """
        Estimate cost for a configuration.
        
        Args:
            config_path: Path to the configuration file
            price_per_gb: Price per GB in USD
            window: Time window for histogram data
            
        Returns:
            Cost estimation results
        """
        return cost.estimate_cost_from_config(
            config_path=config_path,
            price_per_gb=price_per_gb,
            model=cost.COST_MODEL_BLENDED if self.nrdb_client else cost.COST_MODEL_STATIC,
            nrdb_client=self.nrdb_client,
            window=window
        )

    def lint_config(
        self,
        config_path: Path,
        sarif_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Lint a configuration for issues and risks.
        
        Args:
            config_path: Path to the configuration file
            sarif_path: Output path for SARIF report
            
        Returns:
            Lint results
        """
        # Lint the configuration
        lint_results = lint.lint_config(
            config_path=config_path,
            use_nrdb=bool(self.nrdb_client),
            api_key=self.api_key,
            nrdb_client=self.nrdb_client
        )
        
        # Generate SARIF report if requested
        if sarif_path:
            lint.generate_sarif(lint_results, sarif_path)
            
        return lint_results

    def create_rollout_artifacts(
        self,
        config_path: Path,
        hosts_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        mode: str = "ansible",
    ) -> None:
        """
        Create deployment artifacts for configuration rollout.
        
        Args:
            config_path: Path to the configuration file
            hosts_file: Path to hosts file
            output_dir: Output directory for artifacts
            mode: Deployment mode (ansible, script, print)
        """
        rollout.create_deployment_artifacts(
            config_path=config_path,
            hosts_file=hosts_file,
            output_dir=output_dir or self.output_dir / "rollout",
            mode=mode
        )

    def analyze_and_recommend(
        self,
        window: str = "7d",
        entity_filter: Optional[str] = None,
        budget_gb_day: Optional[float] = None,
        max_risk_score: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyze process data and recommend optimal configurations.
        
        Args:
            window: Time window for analysis
            entity_filter: Optional filter for entity name/GUID
            budget_gb_day: Maximum GB per day budget
            max_risk_score: Maximum acceptable risk score
            output_path: Path to save the best configuration
            
        Returns:
            List of configurations ranked by suitability
        """
        if not self.nrdb_client:
            raise ValueError("NRDB client is required for recommendations. Initialize with API key.")
            
        # Get recommendations
        recommendations = analysis.analyze_and_recommend(
            nrdb_client=self.nrdb_client,
            window=window,
            entity_filter=entity_filter,
            budget_gb_day=budget_gb_day,
            max_risk_score=max_risk_score
        )
        
        # Generate the best configuration if requested
        if output_path and recommendations:
            best = recommendations[0]
            analysis.generate_recommended_config(best, output_path)
            
        return recommendations
