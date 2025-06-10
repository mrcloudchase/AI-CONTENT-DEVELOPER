"""
TOC prompts - Backward compatibility imports
This file maintains backward compatibility by importing from the new location
"""
from .phase5.toc_update import (
    get_toc_update_prompt,
    TOC_UPDATE_SYSTEM
)

# Re-export for backward compatibility
__all__ = [
    'get_toc_update_prompt',
    'TOC_UPDATE_SYSTEM'
] 