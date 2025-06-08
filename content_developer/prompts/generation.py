"""
Content generation prompts - Backward compatibility imports
This file maintains backward compatibility by importing from the new location
"""
from .phase3.create_content import (
    get_create_content_prompt,
    CREATE_CONTENT_SYSTEM
)
from .phase3.update_content import (
    get_update_content_prompt,
    UPDATE_CONTENT_SYSTEM
)

# Re-export for backward compatibility
__all__ = [
    'get_create_content_prompt',
    'CREATE_CONTENT_SYSTEM',
    'get_update_content_prompt',
    'UPDATE_CONTENT_SYSTEM'
] 