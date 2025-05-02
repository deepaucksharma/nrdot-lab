"""
Template utilities for Process-Lab.

This module handles the loading and management of templates.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import jinja2


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


def ensure_template_exists(template_name: str, default_content: str) -> Path:
    """
    Ensure a template file exists, creating it with default content if needed.
    
    Args:
        template_name: Name of the template file
        default_content: Default content if the template doesn't exist
        
    Returns:
        Path to the template file
    """
    template_path = get_templates_dir() / template_name
    
    if not template_path.exists():
        # Create the template with default content
        with open(template_path, "w") as f:
            f.write(default_content)
            
    return template_path


def load_yaml_template(template_name: str, default_content: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a YAML template file, creating it with default content if it doesn't exist.
    
    Args:
        template_name: Name of the template file
        default_content: Optional default content if the template doesn't exist
        
    Returns:
        Parsed YAML content
    """
    template_path = get_templates_dir() / template_name
    
    # Create with default content if it doesn't exist
    if not template_path.exists() and default_content:
        with open(template_path, "w") as f:
            f.write(default_content)
    
    # Load the template
    if template_path.exists():
        with open(template_path, "r") as f:
            return yaml.safe_load(f)
    
    # Return empty dict if no template
    return {}


def get_jinja_env() -> jinja2.Environment:
    """
    Get a Jinja2 environment configured for templates.
    
    Returns:
        Jinja2 Environment
    """
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(get_templates_dir()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(
    template_name: str,
    variables: Dict[str, Any],
    default_template: Optional[str] = None
) -> str:
    """
    Render a template with variables.
    
    Args:
        template_name: Name of the template file
        variables: Variables to use in rendering
        default_template: Optional default template content if file doesn't exist
        
    Returns:
        Rendered template as a string
    """
    # Ensure template exists
    if default_template:
        ensure_template_exists(template_name, default_template)
    
    # Get Jinja environment
    env = get_jinja_env()
    
    try:
        # Load and render the template
        template = env.get_template(template_name)
        return template.render(**variables)
    except jinja2.exceptions.TemplateNotFound:
        if default_template:
            # Render default template directly
            template = jinja2.Template(default_template)
            return template.render(**variables)
        else:
            raise ValueError(f"Template '{template_name}' not found")
