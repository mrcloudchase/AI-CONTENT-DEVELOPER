"""
Material processing prompts - Backward compatibility imports
This file maintains backward compatibility by importing from the new location
"""
from .phase1.material_summary import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)

# Re-export for backward compatibility
__all__ = [
    'get_material_summary_prompt',
    'MATERIAL_SUMMARY_SYSTEM'
] 