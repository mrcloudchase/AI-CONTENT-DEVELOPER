"""
Prompts for AI Content Developer
"""

# Material processing prompts
from .material import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)

# Directory selection prompts
from .directory import (
    get_directory_selection_prompt,
    DIRECTORY_SELECTION_SYSTEM
)

# Content strategy prompts
from .strategy import (
    get_unified_content_strategy_prompt,
    UNIFIED_CONTENT_STRATEGY_SYSTEM
)

# Content generation prompts
from .generation import (
    get_create_content_prompt,
    CREATE_CONTENT_SYSTEM,
    get_update_content_prompt,
    UPDATE_CONTENT_SYSTEM
)

# Helper functions
from .helpers import (
    format_semantic_matches,
    format_content_types,
    format_top_chunks,
    format_chunk_clusters,
    format_materials_with_content,
    format_chunks_for_reference,
    get_content_type_template
)

__all__ = [
    # Material prompts
    'get_material_summary_prompt',
    'MATERIAL_SUMMARY_SYSTEM',
    
    # Directory prompts
    'get_directory_selection_prompt',
    'DIRECTORY_SELECTION_SYSTEM',
    
    # Strategy prompts
    'get_unified_content_strategy_prompt',
    'UNIFIED_CONTENT_STRATEGY_SYSTEM',
    
    # Generation prompts
    'get_create_content_prompt',
    'CREATE_CONTENT_SYSTEM',
    'get_update_content_prompt',
    'UPDATE_CONTENT_SYSTEM',
    
    # Helper functions
    'format_semantic_matches',
    'format_content_types',
    'format_top_chunks',
    'format_chunk_clusters',
    'format_materials_with_content',
    'format_chunks_for_reference',
    'get_content_type_template'
]
