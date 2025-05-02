"""
Preset loader implementation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from zcp_core.bus import Event, publish
from zcp_preset.model import Preset


class PresetLoader:
    """
    Loads presets from the filesystem.
    
    Presets can be located in multiple directories, with later directories
    taking precedence (overlay mechanism).
    """
    
    def __init__(self, dirs: Optional[List[str]] = None):
        """
        Initialize the preset loader.
        
        Args:
            dirs: List of directories to search for presets, in order of precedence
                 (later directories override earlier ones)
        """
        self._dirs = dirs or self._default_dirs()
        self._cache: Dict[str, Preset] = {}
        
    @staticmethod
    def _default_dirs() -> List[str]:
        """Get default preset directories."""
        # From lowest to highest precedence
        dirs = []
        
        # Built-in presets
        module_dir = Path(__file__).parent
        dirs.append(str(module_dir / "presets"))
        
        # User presets
        user_preset_dir = os.environ.get("ZCP_PRESET_DIR")
        if user_preset_dir:
            dirs.append(user_preset_dir)
            
        return dirs
    
    def list(self) -> List[str]:
        """
        List available preset IDs.
        
        Returns:
            List of preset IDs
        """
        presets = set()
        
        for directory in self._dirs:
            try:
                path = Path(directory)
                if path.exists() and path.is_dir():
                    for file in path.glob("*.yaml"):
                        presets.add(file.stem)
            except Exception:
                # Skip directories that can't be read
                pass
                
        return sorted(list(presets))
    
    def load(self, id: str) -> Preset:
        """
        Load a preset by ID.
        
        Args:
            id: The preset ID
            
        Returns:
            The loaded preset
            
        Raises:
            FileNotFoundError: If the preset cannot be found
        """
        # Check cache first
        if id in self._cache:
            return self._cache[id]
        
        # Search directories in reverse order (highest precedence first)
        for directory in reversed(self._dirs):
            path = Path(directory) / f"{id}.yaml"
            if path.exists() and path.is_file():
                with open(path, "r") as f:
                    yml = f.read()
                    preset = Preset.from_yaml(yml)
                    
                    # Emit event
                    publish(Event(
                        topic="preset.loaded",
                        payload={
                            "id": preset.id,
                            "hash": preset.sha256
                        }
                    ))
                    
                    # Cache and return
                    self._cache[id] = preset
                    return preset
        
        raise FileNotFoundError(f"Preset not found: {id}")
