"""
Test that all modules in the project can be imported without errors.

This test helps catch issues with missing dependencies, incorrect imports,
or other issues that would cause modules to fail to import.
"""

import importlib
import pkgutil
import pytest


@pytest.mark.parametrize(
    "package_name",
    [
        "zcp_core",
        "zcp_preset",
        "zcp_template",
        "zcp_cost",
        "zcp_lint",
        "zcp_rollout",
        "zcp_validate",
        "zcp_logging",
        "zcp_cli",
    ],
)
def test_package_imports(package_name):
    """Test that all modules in a package can be imported."""
    # Import the package
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        pytest.fail(f"Failed to import package {package_name}: {e}")
        
    # Get all modules in the package
    for _, name, is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        try:
            importlib.import_module(name)
        except ImportError as e:
            pytest.fail(f"Failed to import {name}: {e}")
            
            
def test_model_imports():
    """Test specific model imports that are critical for functionality."""
    # These are the model imports that have been problematic
    critical_imports = {
        "zcp_rollout.models": ["RolloutJob", "RolloutReport", "HostResult"],
        "zcp_validate.models": ["ValidationJob", "ValidationResult"],
        "zcp_cost.plugin": ["CostEstimate", "PluginEstimate", "CostRequest"],
    }
    
    for module_name, class_names in critical_imports.items():
        try:
            module = importlib.import_module(module_name)
            for class_name in class_names:
                assert hasattr(module, class_name), f"{module_name} is missing {class_name}"
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
