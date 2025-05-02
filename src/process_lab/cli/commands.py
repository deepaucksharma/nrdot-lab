"""
Command implementations for the Process-Lab CLI.

This module contains the implementation of all CLI commands.
"""

import os
import sys
import json
import yaml
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from ..core import config as config_module
from ..core import cost as cost_module
from ..core import analysis as analysis_module
from ..utils import lint as lint_module
from ..utils import rollout as rollout_module
from ..client.nrdb import NRDBClient

# Create console for rich output
console = Console()


def get_api_key() -> Optional[str]:
    """Get New Relic API key from environment or prompt."""
    api_key = os.environ.get("NEW_RELIC_API_KEY")
    if not api_key:
        console.print("[yellow]NEW_RELIC_API_KEY environment variable not set[/yellow]")
        api_key = Prompt.ask("Enter your New Relic API key", password=True)
    return api_key


def wizard_command(
    output: Path = typer.Option("./newrelic-infra.yml", "--output", "-o", help="Output path for generated YAML"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key (optional)"),
    skip_cost: bool = typer.Option(False, "--skip-cost", help="Skip cost estimation"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Use a preset configuration"),
) -> None:
    """
    Interactive Q&A to produce optimized YAML.

    Guides you through the process of creating a configuration with
    cost/risk estimates and optional rollout.
    """
    if preset:
        # Get available presets
        available_presets = config_module.list_available_presets()
        preset_names = [p["name"] for p in available_presets]
        
        if preset not in preset_names:
            console.print(f"[red]Error:[/red] Preset '{preset}' not found.")
            console.print(f"Available presets: {', '.join(preset_names)}")
            sys.exit(1)
            
        # Generate config from preset
        console.print(f"Using preset: [bold]{preset}[/bold]")
        yaml_content = config_module.generate_config_from_preset(preset, output)
        
        # Show generated config
        console.print(Panel(
            Syntax(yaml_content, "yaml", line_numbers=True),
            title=f"Generated Configuration ({preset})",
            expand=False
        ))
        
        console.print(f"Configuration written to: [green]{output}[/green]")
        
    else:
        # Interactive wizard
        console.print("[bold blue]New Relic Infrastructure ProcessSample Configuration Wizard[/bold blue]")
        console.print("This wizard will help you create an optimized configuration for the New Relic Infrastructure Agent.")
        
        # Get filter type
        filter_types = config_module.list_available_filter_types()
        filter_type_names = [f["name"] for f in filter_types]
        
        console.print("\n[bold]Available filter types:[/bold]")
        for ft in filter_types:
            console.print(f"  [green]{ft['name']}[/green]: {ft['description']} ({ft['pattern_count']} patterns)")
            
        filter_type = Prompt.ask(
            "Select filter type",
            choices=filter_type_names,
            default="standard"
        )
        
        # Get sample rate
        sample_rate = int(Prompt.ask(
            "Process sample rate (seconds)",
            default="60",
            choices=["20", "30", "60", "90", "120", "180", "300"]
        ))
        
        # Get command line collection
        collect_cmdline = Confirm.ask(
            "Collect command line arguments?",
            default=False
        )
        
        # Generate configuration
        overrides = {"collect_command_line": collect_cmdline}
        yaml_content = config_module.render_agent_yaml(
            sample_rate=sample_rate,
            filter_type=filter_type,
            overrides=overrides
        )
        
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(output, "w") as f:
            f.write(yaml_content)
            
        # Show generated config
        console.print(Panel(
            Syntax(yaml_content, "yaml", line_numbers=True),
            title="Generated Configuration",
            expand=False
        ))
        
        console.print(f"Configuration written to: [green]{output}[/green]")
        
    # Estimate cost if api_key is provided or can be obtained
    if not skip_cost:
        actual_api_key = api_key or get_api_key()
        if actual_api_key:
            estimate_cost_command(
                yaml=output,
                api_key=actual_api_key,
                quiet=False
            )
        else:
            console.print("[yellow]Skipping cost estimation (no API key provided)[/yellow]")
            
    # Check for risks
    lint_command(
        yaml=output,
        api_key=api_key,
        quiet=False
    )
    
    # Ask about rollout
    if Confirm.ask("Generate rollout artifacts?", default=False):
        mode = Prompt.ask(
            "Rollout mode",
            choices=["ansible", "script", "print"],
            default="print"
        )
        
        rollout_command(
            yaml=output,
            mode=mode,
            quiet=False
        )


def generate_config_command(
    sample_rate: int = typer.Option(60, "--sample-rate", "-r", help="Sample rate in seconds (20-300)"),
    filter_type: str = typer.Option("standard", "--filter-type", "-f", help="Filter type (standard, aggressive)"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Template preset name"),
    collect_cmdline: bool = typer.Option(False, "--collect-cmdline", "-c", help="Collect command line arguments"),
    log_file: Optional[str] = typer.Option(None, "--log-file", "-l", help="Log file path"),
    output: Path = typer.Option("./newrelic-infra.yml", "--output", "-o", help="Output path for generated YAML"),
) -> None:
    """
    Non-interactive configuration generator.

    Creates YAML configurations based on command-line options.
    """
    try:
        # Handle preset
        if preset:
            yaml_content = config_module.generate_config_from_preset(preset, output)
            console.print(f"Generated configuration from preset [bold]{preset}[/bold]")
        else:
            # Set up overrides
            overrides = {"collect_command_line": collect_cmdline}
            if log_file:
                overrides["log_file"] = log_file
                
            # Generate configuration
            yaml_content = config_module.render_agent_yaml(
                sample_rate=sample_rate,
                filter_type=filter_type,
                overrides=overrides
            )
            
            # Ensure output directory exists
            output.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(output, "w") as f:
                f.write(yaml_content)
                
            console.print(f"Generated configuration with [bold]rate={sample_rate}s[/bold], [bold]filter={filter_type}[/bold]")
            
        console.print(f"Configuration written to: [green]{output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating configuration:[/red] {e}")
        sys.exit(1)


def list_presets_command() -> None:
    """
    List available configuration presets.
    """
    try:
        presets = config_module.list_available_presets()
        
        if not presets:
            console.print("[yellow]No presets found[/yellow]")
            sys.exit(0)
            
        table = Table(title="Available Configuration Presets")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Sample Rate", justify="right")
        table.add_column("Filter Type")
        
        for preset in presets:
            table.add_row(
                preset["name"],
                preset["description"],
                f"{preset['sample_rate']}s",
                preset["filter_type"]
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing presets:[/red] {e}")
        sys.exit(1)


def list_filters_command() -> None:
    """
    List available filter types.
    """
    try:
        filters = config_module.list_available_filter_types()
        
        if not filters:
            console.print("[yellow]No filter types found[/yellow]")
            sys.exit(0)
            
        table = Table(title="Available Filter Types")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Pattern Count", justify="right")
        
        for filter_type in filters:
            table.add_row(
                filter_type["name"],
                filter_type["description"],
                str(filter_type["pattern_count"])
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing filter types:[/red] {e}")
        sys.exit(1)


def estimate_cost_command(
    yaml: Path = typer.Option(..., "--yaml", "-y", help="Path to YAML config"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    price_per_gb: float = typer.Option(0.35, "--price-per-gb", "-p", help="Price per GB ($)"),
    window: str = typer.Option("6h", "--window", "-w", help="Time window for histogram (e.g., 6h, 1d)"),
    output_json: Optional[Path] = typer.Option(None, "--output-json", "-o", help="Output path for JSON result"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress detailed output"),
) -> None:
    """
    Estimate cost for given configuration.

    Uses the dual-layer cost model to predict GB/day and monthly cost.
    """
    try:
        # Load YAML configuration
        with open(yaml, "r") as f:
            config = yaml.safe_load(f)
            
        # Extract needed parameters
        sample_rate = config.get("metrics_process_sample_rate", 60)
        
        # Calculate keep ratio from excluded metrics
        exclude_metrics = config.get("exclude_matching_metrics", {})
        keep_ratio = 0.92  # Default heuristic
        
        # Dynamic estimation if API key is provided
        actual_api_key = api_key or get_api_key()
        
        if actual_api_key:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Fetching data from NRDB for accurate cost estimation..."),
                transient=True
            ) as progress:
                progress.add_task("fetch", total=1)
                
                # Create NRDB client
                nrdb_client = NRDBClient(api_key=actual_api_key)
                
                # Try to get a more accurate keep ratio
                keep_ratio = lint_module.calculate_keep_ratio(
                    config=config,
                    nrdb_client=nrdb_client,
                    window=window
                )
                
                # Get blended cost estimate
                estimate = cost_module.estimate_cost_blended(
                    sample_rate=sample_rate,
                    keep_ratio=keep_ratio,
                    nrdb_client=nrdb_client,
                    window=window,
                    price_per_gb=price_per_gb
                )
        else:
            # Static model only
            estimate = cost_module.estimate_cost(
                sample_rate=sample_rate,
                keep_ratio=keep_ratio,
                price_per_gb=price_per_gb
            )
            
        # Print results
        if not quiet:
            table = Table(title="Cost Estimation Results")
            table.add_column("Metric", style="bold")
            table.add_column("Value")
            
            table.add_row("Sample Rate", f"{sample_rate} seconds")
            table.add_row("Keep Ratio", f"{keep_ratio:.2f}")
            table.add_row("Data Volume", f"{estimate['gb_day']:.2f} GB/day")
            table.add_row("Monthly Cost", f"${estimate['monthly_cost']:.2f}")
            table.add_row("Confidence", f"{estimate['confidence']:.2f}")
            table.add_row("Estimation Method", estimate['method'])
            
            console.print(table)
            
            if "models" in estimate and len(estimate["models"]) > 1:
                detail_table = Table(title="Model Comparison")
                detail_table.add_column("Model", style="bold")
                detail_table.add_column("GB/day")
                detail_table.add_column("Monthly Cost")
                detail_table.add_column("Confidence")
                
                for model_name, model_data in estimate["models"].items():
                    detail_table.add_row(
                        model_name,
                        f"{model_data.get('gb_day', 0):.2f}",
                        f"${model_data.get('monthly_cost', 0):.2f}",
                        f"{model_data.get('confidence', 0):.2f}"
                    )
                    
                console.print(detail_table)
        else:
            console.print(f"GB/day: {estimate['gb_day']:.2f}, Monthly: ${estimate['monthly_cost']:.2f}")
            
        # Save JSON output if requested
        if output_json:
            with open(output_json, "w") as f:
                json.dump(estimate, f, indent=2)
                
            if not quiet:
                console.print(f"Detailed estimation saved to: [green]{output_json}[/green]")
                
        return estimate
        
    except Exception as e:
        console.print(f"[red]Error estimating cost:[/red] {e}")
        sys.exit(1)


def validate_command(
    yaml: Path = typer.Option(..., "--yaml", "-y", help="Path to YAML config"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    window: str = typer.Option("1d", "--window", "-w", help="Time window (e.g., 1d, 7d)"),
    account_id: Optional[int] = typer.Option(None, "--account-id", "-a", help="New Relic account ID"),
) -> None:
    """
    Validate actual costs and coverage after deployment.

    Queries NRDB to check real-world performance against predictions.
    """
    try:
        # Get API key if not provided
        actual_api_key = api_key or get_api_key()
        if not actual_api_key:
            console.print("[red]API key is required for validation[/red]")
            sys.exit(1)
            
        # Create NRDB client
        nrdb_client = NRDBClient(api_key=actual_api_key)
        
        # Load YAML configuration
        with open(yaml, "r") as f:
            config = yaml.safe_load(f)
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Querying NRDB for validation data..."),
            transient=True
        ) as progress:
            progress.add_task("fetch", total=1)
            
            # TODO: Implement actual validation
            # This would fetch actual data from NRDB and compare against predictions
            
            # Placeholder for now
            console.print("[yellow]Validation functionality not yet fully implemented[/yellow]")
            console.print("This would query NRDB to verify:\n1. Actual data volume\n2. Coverage of critical processes\n3. Comparison against predictions")
            
    except Exception as e:
        console.print(f"[red]Error validating configuration:[/red] {e}")
        sys.exit(1)


def lint_command(
    yaml: Path = typer.Option(..., "--yaml", "-y", help="Path to YAML config"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    sarif: Optional[Path] = typer.Option(None, "--sarif", "-s", help="Output path for SARIF report"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress detailed output"),
) -> None:
    """
    Check YAML config for risks and issues.

    Runs risk heuristics and schema validation.
    """
    try:
        # Get API key (optional)
        actual_api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        
        # Lint the configuration
        lint_results = lint_module.lint_config(
            config_path=yaml,
            use_nrdb=bool(actual_api_key),
            api_key=actual_api_key
        )
        
        # Display results
        if not quiet:
            # Display risk score
            risk_color = "green"
            if lint_results["risk_score"] >= 7:
                risk_color = "red"
            elif lint_results["risk_score"] >= 4:
                risk_color = "yellow"
                
            console.print(f"Risk Score: [{risk_color}]{lint_results['risk_score']}/10[/{risk_color}]")
            
            if lint_results["high_risk"]:
                console.print("[red bold]High Risk Configuration![/red bold]")
                
            # Display issues
            if lint_results["issues"]:
                table = Table(title="Configuration Issues")
                table.add_column("Rule", style="cyan")
                table.add_column("Level", style="bold")
                table.add_column("Message")
                
                for issue in lint_results["issues"]:
                    level_style = {
                        "error": "red",
                        "warning": "yellow",
                        "info": "blue",
                    }.get(issue["level"], "white")
                    
                    table.add_row(
                        issue["rule"],
                        f"[{level_style}]{issue['level']}[/{level_style}]",
                        issue["message"]
                    )
                    
                console.print(table)
            else:
                console.print("[green]No issues found![/green]")
                
            # Note about NRDB usage
            if lint_results.get("used_nrdb", False):
                console.print("[blue]Used NRDB data for dynamic analysis[/blue]")
            else:
                console.print("[yellow]Using static analysis only (no NRDB data)[/yellow]")
        else:
            # Quiet output
            console.print(f"Risk: {lint_results['risk_score']}/10, Issues: {len(lint_results['issues'])}")
            
        # Generate SARIF report if requested
        if sarif:
            sarif_json = lint_module.generate_sarif(lint_results, sarif)
            if not quiet:
                console.print(f"SARIF report saved to: [green]{sarif}[/green]")
                
        return lint_results
        
    except Exception as e:
        console.print(f"[red]Error linting configuration:[/red] {e}")
        sys.exit(1)


def rollout_command(
    yaml: Path = typer.Option(..., "--yaml", "-y", help="Path to YAML config"),
    mode: str = typer.Option("print", "--mode", "-m", help="Rollout mode (ansible, script, print)"),
    hosts_file: Optional[Path] = typer.Option(None, "--hosts-file", "-h", help="Path to hosts file (JSON)"),
    output_dir: Path = typer.Option("./rollout_artifacts", "--output-dir", "-o", help="Output directory for artifacts"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress detailed output"),
) -> None:
    """
    Create deployment artifacts for configuration rollout.

    Supports Ansible, script generation, or printing commands.
    """
    try:
        # Check that the config file exists
        if not yaml.exists():
            console.print(f"[red]Config file not found: {yaml}[/red]")
            sys.exit(1)
            
        # Create deployment artifacts
        if mode == "print":
            # Print mode just displays commands
            rollout_module.print_rollout_help(yaml)
        else:
            # Create artifacts
            rollout_module.create_deployment_artifacts(
                config_path=yaml,
                hosts_file=hosts_file,
                output_dir=output_dir,
                mode=mode
            )
            
            if not quiet:
                console.print(f"[green]Created {mode} deployment artifacts in {output_dir}[/green]")
                console.print("\n[yellow]Remember to review the generated files before deploying[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error creating rollout artifacts:[/red] {e}")
        sys.exit(1)


def visualize_command(
    yaml: Path = typer.Option(..., "--yaml", "-y", help="Path to YAML config"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    window: str = typer.Option("7d", "--window", "-w", help="Time window (e.g., 1d, 7d)"),
    output_dir: Path = typer.Option("./visualizations", "--output-dir", "-o", help="Output directory for visualizations"),
) -> None:
    """
    Generate visualizations of configuration impact.

    Creates charts showing keep ratio, cost savings, etc.
    """
    try:
        console.print("[yellow]Visualization functionality not yet implemented[/yellow]")
        console.print("This would generate charts showing the impact of your configuration.")
        console.print("For now, please use the NRDB dashboards created by the 'nrdb pull-pack' command.")
        
    except Exception as e:
        console.print(f"[red]Error generating visualizations:[/red] {e}")
        sys.exit(1)


def recommend_command(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    window: str = typer.Option("7d", "--window", "-w", help="Time window (e.g., 1d, 7d)"),
    entity_filter: Optional[str] = typer.Option(None, "--entity", "-e", help="Entity filter (hostname or GUID)"),
    output: Path = typer.Option("./config/newrelic-infra.yml", "--output", "-o", help="Output path for generated YAML"),
    budget_gb: Optional[float] = typer.Option(None, "--budget-gb", "-b", help="Maximum GB per day budget"),
    max_risk: Optional[int] = typer.Option(None, "--max-risk", "-r", help="Maximum acceptable risk score (0-10)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
) -> None:
    """
    Recommend an optimal configuration based on NRDB data.

    Analyzes actual process data to suggest an optimized configuration.
    """
    try:
        # Get API key if not provided
        actual_api_key = api_key or get_api_key()
        if not actual_api_key:
            console.print("[red]API key is required for recommendations[/red]")
            sys.exit(1)
            
        # Create NRDB client
        nrdb_client = NRDBClient(api_key=actual_api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Analyzing process data from NRDB..."),
            transient=True
        ) as progress:
            progress.add_task("analyze", total=1)
            
            # Get recommendations
            recommendations = analysis_module.analyze_and_recommend(
                nrdb_client=nrdb_client,
                window=window,
                entity_filter=entity_filter,
                budget_gb_day=budget_gb,
                max_risk_score=max_risk
            )
            
        # Display recommendations
        if format.lower() == "json":
            # Output as JSON
            if output.suffix.lower() == ".json":
                json_path = output
            else:
                json_path = output.with_suffix(".json")
                
            with open(json_path, "w") as f:
                json.dump(recommendations, f, indent=2)
                
            console.print(f"Saved {len(recommendations)} recommendations to: [green]{json_path}[/green]")
        else:
            # Display as table
            if recommendations:
                table = Table(title="Configuration Recommendations")
                table.add_column("Rank", style="cyan", justify="right")
                table.add_column("Sample Rate", justify="right")
                table.add_column("Filter Type")
                table.add_column("GB/day", justify="right")
                table.add_column("Monthly Cost", justify="right")
                table.add_column("Risk", justify="right")
                table.add_column("Keep %", justify="right")
                
                for rec in recommendations[:5]:  # Show top 5
                    cost_value = f"${rec['est_monthly_cost']:.2f}"
                    table.add_row(
                        str(rec["rank"]),
                        f"{rec['sample_rate']}s",
                        rec["filter_type"],
                        f"{rec['est_gb_day']:.2f}",
                        cost_value,
                        str(rec["risk_score"]),
                        f"{rec['keep_ratio']*100:.1f}%"
                    )
                
                console.print(table)
                
                # Select the best recommendation
                best = recommendations[0]
                console.print(f"\nBest configuration: [bold]{best['filter_type']}[/bold] filter with [bold]{best['sample_rate']}s[/bold] sample rate")
                console.print(f"Estimated cost: ${best['est_monthly_cost']:.2f}/month ({best['est_gb_day']:.2f} GB/day)")
                console.print(f"Risk score: {best['risk_score']}/10, Keep ratio: {best['keep_ratio']*100:.1f}%")
                
                # Generate and save the recommended configuration
                if Confirm.ask("Generate this configuration?", default=True):
                    yaml_content = analysis_module.generate_recommended_config(best, output)
                    console.print(f"Configuration saved to: [green]{output}[/green]")
            else:
                console.print("[yellow]No suitable recommendations found.[/yellow]")
                console.print("Try adjusting constraints like budget or max risk score.")
            
    except Exception as e:
        console.print(f"[red]Error generating recommendation:[/red] {e}")
        sys.exit(1)


def nrdb_command(
    command: str = typer.Argument(..., help="NRDB command (pull-pack, list-dashboards)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="New Relic API key"),
    output_dir: Path = typer.Option("./nrdb_analysis", "--output-dir", "-o", help="Output directory for NRQL pack"),
) -> None:
    """
    NRDB-related commands.

    Interact with NRDB for dashboards and saved queries.
    """
    try:
        # Get API key if not provided
        actual_api_key = api_key or get_api_key()
        if not actual_api_key:
            console.print("[red]API key is required for NRDB operations[/red]")
            sys.exit(1)
            
        # Create NRDB client
        nrdb_client = NRDBClient(api_key=actual_api_key)
        
        if command == "pull-pack":
            console.print("[yellow]NRQL pack functionality not yet implemented[/yellow]")
            console.print("This would pull predefined NRQL queries and dashboards into your account.")
            
        elif command == "list-dashboards":
            console.print("[yellow]Dashboard listing functionality not yet implemented[/yellow]")
            console.print("This would list available ProcessSample dashboards in your account.")
            
        else:
            console.print(f"[red]Unknown NRDB command: {command}[/red]")
            console.print("Available commands: pull-pack, list-dashboards")
            
    except Exception as e:
        console.print(f"[red]Error executing NRDB command:[/red] {e}")
        sys.exit(1)
