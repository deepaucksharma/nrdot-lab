"""
Template renderer implementation.
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import jinja2
from pydantic import BaseModel, Field

from zcp_core.bus import Event, publish


class TokensBase(BaseModel):
    """
    Base class for template tokens.
    """
    preset_id: str
    sample_rate: int
    filter_mode: str
    filter_patterns: List[str]


class TokensInfra(TokensBase):
    """
    Tokens for Infrastructure agent templates.
    """
    exporter_headers: Dict[str, str] = Field(default_factory=dict)


class TokensOtel(TokensBase):
    """
    Tokens for OpenTelemetry agent templates.
    """
    resource_attrs: Dict[str, str] = Field(default_factory=dict)
    processors_block: str = ""


class RenderRequest(BaseModel):
    """
    Template rendering request.
    """
    template_id: str
    tokens: Union[TokensBase, TokensInfra, TokensOtel]


class RenderedYAML(BaseModel):
    """
    Rendered template result.
    """
    text: str
    checksum: str
    duration_ms: float


class TemplateRenderer:
    """
    Renders templates with provided tokens.
    """
    
    def __init__(self, template_dirs: Optional[List[str]] = None):
        """
        Initialize the template renderer.
        
        Args:
            template_dirs: List of directories to search for templates
        """
        self._dirs = template_dirs or self._default_dirs()
        
        # Set up Jinja environment
        loader = jinja2.FileSystemLoader(self._dirs)
        self._env = jinja2.Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )
    
    @staticmethod
    def _default_dirs() -> List[str]:
        """Get default template directories."""
        dirs = []
        
        # Built-in templates
        module_dir = Path(__file__).parent
        dirs.append(str(module_dir / "templates"))
        
        # User templates
        user_template_dir = os.environ.get("ZCP_TEMPLATE_DIR")
        if user_template_dir:
            dirs.append(user_template_dir)
            
        return dirs
    
    def render(self, req: RenderRequest) -> RenderedYAML:
        """
        Render a template with provided tokens.
        
        Args:
            req: Render request
            
        Returns:
            Rendered template
            
        Raises:
            jinja2.exceptions.TemplateNotFound: If template not found
            jinja2.exceptions.TemplateError: If template rendering fails
        """
        start_time = time.time()
        
        # Load template
        template = self._env.get_template(f"{req.template_id}.yaml.j2")
        
        # Render
        result = template.render(**req.tokens.dict())
        
        # Calculate duration and checksum
        duration_ms = (time.time() - start_time) * 1000
        checksum = hashlib.sha256(result.encode()).hexdigest()
        
        # Create result
        rendered = RenderedYAML(
            text=result,
            checksum=checksum,
            duration_ms=duration_ms
        )
        
        # Publish event
        publish(Event(
            topic="template.rendered",
            payload={
                "template_id": req.template_id,
                "checksum": checksum,
                "duration_ms": duration_ms
            }
        ))
        
        return rendered
    
    def validate(self, text: str) -> None:
        """
        Validate rendered YAML.
        
        Args:
            text: YAML text to validate
            
        Raises:
            ValueError: If validation fails
        """
        # This is a placeholder for more complex validation
        # In a real implementation, we would check things like:
        # - Valid YAML syntax
        # - Required fields are present
        # - Values are within expected ranges
        
        if not text or not text.strip():
            raise ValueError("Template generated empty output")
