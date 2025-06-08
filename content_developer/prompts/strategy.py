"""
Strategy prompts - Backward compatibility imports
This file maintains backward compatibility by importing from the new location
"""
from .phase2.unified_strategy import (
    get_unified_content_strategy_prompt,
    UNIFIED_CONTENT_STRATEGY_SYSTEM
)

# Re-export for backward compatibility
__all__ = [
    'get_unified_content_strategy_prompt',
    'UNIFIED_CONTENT_STRATEGY_SYSTEM'
]
