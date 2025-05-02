"""
Configuration generator for New Relic Infrastructure Agent.

This module handles the generation of YAML configurations based on templates.
"""

import os
import datetime
from typing import Dict, Any, Optional, List, Union
import yaml
from pathlib import Path
import jinja2
from importlib import resources


# Constants
COST_MODEL_STATIC = "static"
COST_MODEL_DYNAMIC = "histogram"
COST_MODEL_BLENDED = "blended"


def get_templates_dir() -> Path:
    """
    Get the path to the templates directory.
    
    Returns:
        Path to the templates directory
    """
    # Primary location: templates within the package
    templates_path = Path(__file__).parent.parent / "templates"
    
    # Create if it doesn't exist
    if not templates_path.exists():
        templates_path.mkdir(parents=True, exist_ok=True)
        
    return templates_path


def load_filter_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Load filter definitions from the YAML file.
    
    Returns:
        Dictionary of filter definitions
    """
    filter_defs_path = get_templates_dir() / "filter-definitions.yml"
    
    if not filter_defs_path.exists():
        # Create a default filter definitions file if it doesn't exist
        default_filters = {
            "filters": {
                "standard": {
                    "description": "Standard filter set for common background processes",
                    "patterns": {
                        "process.chrome.*": True,
                        "process.firefox.*": True,
                        "process.edge.*": True,
                        "process.safari.*": True,
                        "process.slack.*": True,
                        "process.teams.*": True,
                        "process.zoom.*": True,
                        "process.vscode.*": True,
                        "process.code.*": True,
                        "process.spotify.*": True,
                    }
                },
                "aggressive": {
                    "description": "Aggressive filter set with maximum filtering",
                    "patterns": {
                        "process.chrome.*": True,
                        "process.firefox.*": True,
                        "process.edge.*": True,
                        "process.safari.*": True,
                        "process.slack.*": True,
                        "process.teams.*": True,
                        "process.zoom.*": True,
                        "process.vscode.*": True,
                        "process.code.*": True,
                        "process.spotify.*": True,
                        "process.*tmp*": True,
                        "process.*cache*": True,
                        "process.*daemon*": True,
                        "process.*helper*": True,
                        "process.*notifier*": True,
                        "process.*updater*": True,
                        "process.*background*": True,
                        # Except critical processes
                        "process.nginx.*": False,
                        "process.java.*": False,
                        "process.node.*": False,
                        "process.python*": False,
                        "process.ruby*": False,
                        "process.php*": False,
                        "process.mysqld*": False,
                        "process.postgres*": False,
                        "process.redis*": False,
                        "process.mongo*": False,
                    }
                },
                "minimal": {
                    "description": "Minimal filter set for testing",
                    "patterns": {
                        "process.chrome.*": True,
                        "process.firefox.*": True,
                    }
                }
            }
        }
        
        # Create the templates directory if it doesn't exist
        filter_defs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default filters
        with open(filter_defs_path, "w") as f:
            yaml.dump(default_filters, f, sort_keys=False)
            
        return default_filters["filters"]
    
    # Load filters from file
    with open(filter_defs_path, "r") as f:
        filters = yaml.safe_load(f)
    
    return filters.get("filters", {})


def load_wizard_presets() -> Dict[str, Dict[str, Any]]:
    """
    Load wizard presets from the YAML file.
    
    Returns:
        Dictionary of wizard presets
    """
    presets_path = get_templates_dir() / "wizard-presets.yml"
    
    if not presets_path.exists():
        # Create a default presets file if it doesn't exist
        default_presets = {
            "presets": {
                "web_standard": {
                    "description": "Generic Nginx + Node stack",
                    "sample_rate": 90,
                    "filter_type": "aggressive",
                    "overrides": {
                        "exclude_matching_metrics": {
                            "process.nginx.*": False,
                            "process.node.*": False,
                        }
                    }
                },
                "jvm_large": {
                    "description": "Large JVM app server",
                    "sample_rate": 30,
                    "filter_type": "standard",
                    "overrides": {
                        "collect_command_line": True,
                    }
                },
                "db_server": {
                    "description": "Database server (MySQL, PostgreSQL)",
                    "sample_rate": 60,
                    "filter_type": "aggressive",
                    "overrides": {
                        "exclude_matching_metrics": {
                            "process.mysqld.*": False,
                            "process.postgres.*": False,
                            "process.redis.*": False,
                            "process.mongo.*": False,
                        }
                    }
                }
            }
        }
        
        # Create the templates directory if it doesn't exist
        presets_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default presets
        with open(presets_path, "w") as f:
            yaml.dump(default_presets, f, sort_keys=False)
            
        return default_presets["presets"]
    
    # Load presets from file
    with open(presets_path, "r") as f:
        presets = yaml.safe_load(f)
    
    return presets.get("presets", {})


def create_template_if_missing(template_dir: Path) -> None:
    """
    Create the template file if it doesn't exist.
    
    Args:
        template_dir: Path to the templates directory
    """
    template_path = template_dir / "newrelic-infra.tpl.yaml"
    
    if not template_path.exists():
        # Create a default template
        default_template = """# Generated {{ timestamp }} by process-lab
#
# Sample rate: {{ sample_rate }}s
# Filter type: {{ filter_type }}

metrics_process_sample_rate: {{ sample_rate }}
exclude_matching_metrics:
{% for pattern, excluded in filter_patterns.items() %}
  {{ pattern }}: {{ excluded | lower }}
{% endfor %}
{% if collect_command_line is defined %}
collect_command_line: {{ collect_command_line | lower }}
{% else %}
collect_command_line: false
{% endif %}
{% if log_file is defined %}
log_file: {{ log_file }}
{% endif %}
"""
        
        # Create the templates directory if it doesn't exist
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default template
        with open(template_path, "w") as f:
            f.write(default_template)


def render_agent_yaml(
    sample_rate: int,
    filter_type: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render the New Relic Infrastructure Agent YAML configuration.
    
    Args:
        sample_rate: Process sample rate in seconds
        filter_type: Filter type (standard, aggressive)
        overrides: Additional overrides for the template
        
    Returns:
        Rendered YAML configuration as a string
    """
    # Load filter definitions
    filters = load_filter_definitions()
    
    # Get the filter patterns
    if filter_type not in filters:
        raise ValueError(f"Unknown filter type: {filter_type}")
    
    filter_patterns = filters[filter_type]["patterns"]
    
    # Set up Jinja environment
    template_dir = get_templates_dir()
    
    # Ensure template exists
    create_template_if_missing(template_dir)
    
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    # Load the template
    template = env.get_template("newrelic-infra.tpl.yaml")
    
    # Prepare template context
    context = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sample_rate": sample_rate,
        "filter_type": filter_type,
        "filter_patterns": filter_patterns,
    }
    
    # Apply overrides
    if overrides:
        # Handle special case for exclude_matching_metrics
        if "exclude_matching_metrics" in overrides:
            # Merge with existing patterns, with overrides taking precedence
            merged_patterns = {**filter_patterns, **overrides["exclude_matching_metrics"]}
            context["filter_patterns"] = merged_patterns
            
            # Remove from overrides to avoid double-application
            overrides_copy = {k: v for k, v in overrides.items() if k != "exclude_matching_metrics"}
            context.update(overrides_copy)
        else:
            context.update(overrides)
    
    # Render template
    return template.render(**context)


def generate_config_from_preset(
    preset_name: str,
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate a configuration from a preset.
    
    Args:
        preset_name: Name of the preset
        output_path: Path to write the configuration to (optional)
        
    Returns:
        Rendered YAML configuration as a string
    """
    # Load presets
    presets = load_wizard_presets()
    
    # Get the preset
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}")
    
    preset = presets[preset_name]
    
    # Render YAML
    yaml_str = render_agent_yaml(
        sample_rate=preset["sample_rate"],
        filter_type=preset["filter_type"],
        overrides=preset.get("overrides"),
    )
    
    # Write to file if output path provided
    if output_path:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(yaml_str)
    
    return yaml_str


def list_available_presets() -> List[Dict[str, Any]]:
    """
    List all available presets.
    
    Returns:
        List of preset information dictionaries
    """
    presets = load_wizard_presets()
    
    result = []
    for name, preset in presets.items():
        result.append({
            "name": name,
            "description": preset.get("description", ""),
            "sample_rate": preset.get("sample_rate", 60),
            "filter_type": preset.get("filter_type", "standard"),
        })
    
    return result


def list_available_filter_types() -> List[Dict[str, Any]]:
    """
    List all available filter types.
    
    Returns:
        List of filter type information dictionaries
    """
    filters = load_filter_definitions()
    
    result = []
    for name, filter_def in filters.items():
        result.append({
            "name": name,
            "description": filter_def.get("description", ""),
            "pattern_count": len(filter_def.get("patterns", {})),
        })
    
    return result


def create_custom_filter(
    name: str,
    description: str,
    patterns: Dict[str, bool],
    overwrite: bool = False,
) -> bool:
    """
    Create a custom filter definition.
    
    Args:
        name: Name of the filter
        description: Description of the filter
        patterns: Dictionary of patterns and exclusion flags
        overwrite: Whether to overwrite existing filter
        
    Returns:
        True if successful, False otherwise
    """
    # Load existing filters
    filters = load_filter_definitions()
    
    # Check if filter already exists
    if name in filters and not overwrite:
        return False
    
    # Add new filter
    filters[name] = {
        "description": description,
        "patterns": patterns,
    }
    
    # Write to file
    filter_defs_path = get_templates_dir() / "filter-definitions.yml"
    
    with open(filter_defs_path, "w") as f:
        yaml.dump({"filters": filters}, f, sort_keys=False)
    
    return True
