"""
Compatibility module for handling differences between Python versions and libraries.
"""

import asyncio
import sys
import importlib.util
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

# Async compatibility for Python 3.11+
def get_or_create_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current event loop or create a new one safely.
    
    This function works around the Python 3.11+ deprecation of get_event_loop()
    when no loop is running.
    
    Returns:
        Current event loop or a new event loop
    """
    try:
        # Try to get the running loop (works in all Python versions)
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # No loop is running
        if sys.version_info >= (3, 11):
            # In Python 3.11+, asyncio.get_event_loop() raises a DeprecationWarning
            # when no loop is running, use new_event_loop() instead
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        else:
            # In Python <= 3.10, get_event_loop() still works
            return asyncio.get_event_loop()

# Pydantic compatibility
def is_pydantic_v2() -> bool:
    """Check if Pydantic v2 is installed."""
    try:
        import pydantic.v1  # Only exists in Pydantic v2
        return True
    except ImportError:
        try:
            import pydantic
            return pydantic.__version__.startswith("2.")
        except (ImportError, AttributeError):
            return False

# Import the appropriate Pydantic version
if is_pydantic_v2():
    try:
        # Pydantic v2 with v1 compatibility
        from pydantic.v1 import (
            BaseModel,
            Field,
            validator,
            root_validator,
            create_model,
            ValidationError,
        )
    except ImportError:
        # Direct v2 import if v1 compatibility not available
        from pydantic import (
            BaseModel,
            Field,
            field_validator as validator,
            model_validator as root_validator,
            create_model,
            ValidationError,
        )
else:
    # Pydantic v1
    from pydantic import (
        BaseModel,
        Field,
        validator,
        root_validator,
        create_model,
        ValidationError,
    )

# Model helper for v1/v2 compatibility
T = TypeVar('T', bound='PydanticCompatModel')

class PydanticCompatModel(BaseModel):
    """
    Base model with compatibility methods for Pydantic v1 and v2.
    
    Inherit from this instead of directly from BaseModel for forward compatibility.
    """
    
    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Dict method that works in both v1 and v2."""
        if is_pydantic_v2():
            # In v2, .dict() is replaced with .model_dump()
            if hasattr(super(), "model_dump"):
                return super().model_dump(*args, **kwargs)
        # Fall back to v1 behavior
        return super().dict(*args, **kwargs)
    
    @classmethod
    def parse_obj(cls: Type[T], obj: Any) -> T:
        """Parse object method that works in both v1 and v2."""
        if is_pydantic_v2():
            # In v2, parse_obj is replaced with model_validate
            if hasattr(cls, "model_validate"):
                validate_method = cast(Callable[[Any], T], getattr(cls, "model_validate"))
                return validate_method(obj)
        # Fall back to v1 behavior
        if hasattr(cls, "parse_obj"):
            return cast(Callable[[Any], T], getattr(cls, "parse_obj"))(obj)
        # Last resort - direct instantiation
        return cls(**obj)
