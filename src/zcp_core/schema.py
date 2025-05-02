"""
Schema validation module for ZCP component contracts.

Handles JSON Schema validation against registered schemas in the schema registry.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import jsonschema
from jsonschema import ValidationError

# Default schema directory
SCHEMA_DIR = os.environ.get("ZCP_SCHEMA_DIR", None)

def _find_schema_dir() -> Path:
    """Find the schema directory."""
    if SCHEMA_DIR:
        return Path(SCHEMA_DIR)
    
    # Try to find it relative to this file
    current_dir = Path(__file__).parent
    
    # Check if we're in src/zcp_core
    if current_dir.name == "zcp_core" and current_dir.parent.name == "src":
        return current_dir.parent.parent / "schema"
    
    # Default to current working directory
    return Path.cwd() / "schema"

def load_schema(schema_id: str, version: int = 1) -> Dict[str, Any]:
    """
    Load a JSON schema from the schema registry.
    
    Args:
        schema_id: The schema identifier (e.g., "CostEstimate")
        version: The schema version (default: 1)
        
    Returns:
        The loaded schema as a dictionary
        
    Raises:
        FileNotFoundError: If the schema cannot be found
        json.JSONDecodeError: If the schema is not valid JSON
    """
    schema_dir = _find_schema_dir()
    schema_path = schema_dir / f"v{version}" / f"{schema_id}.schema.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return json.load(f)

def validate(obj: Any, schema_id: str, version: int = 1) -> None:
    """
    Validate an object against a JSON schema.
    
    Args:
        obj: The object to validate
        schema_id: The schema identifier (e.g., "CostEstimate")
        version: The schema version (default: 1)
        
    Raises:
        ValidationError: If the object does not conform to the schema
        FileNotFoundError: If the schema cannot be found
        json.JSONDecodeError: If the schema is not valid JSON
    """
    schema = load_schema(schema_id, version)
    jsonschema.validate(instance=obj, schema=schema)

def is_valid(obj: Any, schema_id: str, version: int = 1) -> bool:
    """
    Check if an object is valid against a JSON schema.
    
    Args:
        obj: The object to validate
        schema_id: The schema identifier (e.g., "CostEstimate")
        version: The schema version (default: 1)
        
    Returns:
        True if the object is valid, False otherwise
    """
    try:
        validate(obj, schema_id, version)
        return True
    except (ValidationError, FileNotFoundError, json.JSONDecodeError):
        return False
