"""
ZCP Core package containing shared utilities and base components.
"""

__version__ = "0.1.1"

from zcp_core.compat import is_pydantic_v2

# Log Pydantic version on import
import logging
logger = logging.getLogger(__name__)

if is_pydantic_v2():
    logger.debug("Using Pydantic v2 with compatibility layer")
else:
    logger.debug("Using Pydantic v1")
