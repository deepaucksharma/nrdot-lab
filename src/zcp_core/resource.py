"""
Resource loader for templates, presets, schemas and other data files.

This module provides a consistent way to access packaged resources
whether running from source or from an installed wheel.
"""

import importlib.resources
import os
from pathlib import Path
from typing import Optional, Union


def get_resource_path(package_name: str, resource_dir: str, resource_name: str) -> Path:
    """
    Get a path to a resource file, handling both development and installed mode.
    
    Args:
        package_name: Name of the package containing the resource (e.g., 'zcp_template')
        resource_dir: Directory within the package (e.g., 'templates')
        resource_name: Name of the resource file
        
    Returns:
        Path to the resource
    """
    # First try importlib.resources for Python 3.9+
    try:
        with importlib.resources.files(f"{package_name}.{resource_dir}").joinpath(resource_name) as path:
            return path
    except (ImportError, ModuleNotFoundError, AttributeError, FileNotFoundError):
        pass
        
    # Then try direct file path for development mode
    try:
        package_module = importlib.import_module(package_name)
        package_path = Path(package_module.__file__).parent
        resource_path = package_path / resource_dir / resource_name
        if resource_path.exists():
            return resource_path
    except (ImportError, AttributeError, TypeError):
        pass
        
    # Finally try alternate locations for installed packages
    # This handles cases where resources are installed at the package level
    try:
        # Try to locate the package installation directory
        package_module = importlib.import_module(package_name)
        package_path = Path(package_module.__file__).parent
        
        # Check if resources are at the root level of the package
        resource_path = package_path / resource_name
        if resource_path.exists():
            return resource_path
            
        # Check for a 'resources' directory
        resource_path = package_path / 'resources' / resource_dir / resource_name
        if resource_path.exists():
            return resource_path
    except (ImportError, AttributeError, TypeError):
        pass
        
    # If none of the methods worked, raise an error
    raise FileNotFoundError(f"Could not locate resource {resource_name} in {package_name}.{resource_dir}")


def read_resource(package_name: str, resource_dir: str, resource_name: str) -> str:
    """
    Read a resource file as text.
    
    Args:
        package_name: Name of the package containing the resource (e.g., 'zcp_template')
        resource_dir: Directory within the package (e.g., 'templates')
        resource_name: Name of the resource file
        
    Returns:
        Content of the resource file as text
    """
    resource_path = get_resource_path(package_name, resource_dir, resource_name)
    return resource_path.read_text(encoding='utf-8')


def list_resources(package_name: str, resource_dir: str) -> list[str]:
    """
    List all resources in a directory.
    
    Args:
        package_name: Name of the package containing the resources
        resource_dir: Directory within the package
        
    Returns:
        List of resource names
    """
    # Try importlib.resources for Python 3.9+
    try:
        resources = []
        with importlib.resources.files(f"{package_name}.{resource_dir}") as path:
            for item in path.iterdir():
                if item.is_file():
                    resources.append(item.name)
        if resources:
            return resources
    except (ImportError, ModuleNotFoundError, AttributeError, FileNotFoundError):
        pass
        
    # Try direct file path for development mode
    try:
        package_module = importlib.import_module(package_name)
        package_path = Path(package_module.__file__).parent
        resource_path = package_path / resource_dir
        
        if resource_path.exists() and resource_path.is_dir():
            return [item.name for item in resource_path.iterdir() if item.is_file()]
    except (ImportError, AttributeError, TypeError):
        pass
        
    # If none of the methods worked, raise an error
    raise FileNotFoundError(f"Could not locate resource directory {resource_dir} in {package_name}")
