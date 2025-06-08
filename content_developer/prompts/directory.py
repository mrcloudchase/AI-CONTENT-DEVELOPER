"""
Directory selection prompts - Backward compatibility imports
This file maintains backward compatibility by importing from the new location
"""
from .phase1.directory_selection import (
    get_directory_selection_prompt,
    DIRECTORY_SELECTION_SYSTEM
)

# Re-export for backward compatibility
__all__ = [
    'get_directory_selection_prompt',
    'DIRECTORY_SELECTION_SYSTEM'
] 