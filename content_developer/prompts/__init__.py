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

# Strategy prompts
from .strategy import (
    get_unified_content_strategy_prompt,
    UNIFIED_CONTENT_STRATEGY_SYSTEM
)

# Generation prompts
from .generation import (
    get_create_content_prompt,
    CREATE_CONTENT_SYSTEM,
    get_update_content_prompt,
    UPDATE_CONTENT_SYSTEM
)

# TOC prompts
from .toc import (
    get_toc_update_prompt,
    TOC_UPDATE_SYSTEM
)

# LLM-Native prompts
from .llm_native import (
    DOCUMENT_STRUCTURE_SYSTEM,
    get_document_structure_prompt,
    CONTENT_PLACEMENT_SYSTEM,
    get_content_placement_prompt,
    TERMINAL_SECTION_SYSTEM,
    get_terminal_section_prompt,
    get_content_quality_system,
    get_content_quality_prompt,
    INFORMATION_EXTRACTION_SYSTEM,
    get_information_extraction_prompt,
    TOC_PLACEMENT_SYSTEM,
    get_toc_placement_prompt,
    CONTENT_INTENT_SYSTEM,
    get_content_intent_prompt,
    CHUNK_RANKING_SYSTEM,
    get_chunk_ranking_prompt
)

# Helper functions
from .helpers import (
    format_materials_with_content,
    format_chunks_for_reference,
    get_content_type_template,
    format_microsoft_elements
)

__all__ = [
    # Material processing
    'get_material_summary_prompt',
    'MATERIAL_SUMMARY_SYSTEM',
    
    # Directory selection
    'get_directory_selection_prompt',
    'DIRECTORY_SELECTION_SYSTEM',
    
    # Strategy
    'get_unified_content_strategy_prompt',
    'UNIFIED_CONTENT_STRATEGY_SYSTEM',
    
    # Generation
    'get_create_content_prompt',
    'CREATE_CONTENT_SYSTEM',
    'get_update_content_prompt',
    'UPDATE_CONTENT_SYSTEM',
    
    # TOC
    'get_toc_update_prompt',
    'TOC_UPDATE_SYSTEM',
    
    # LLM-Native
    'DOCUMENT_STRUCTURE_SYSTEM',
    'get_document_structure_prompt',
    'CONTENT_PLACEMENT_SYSTEM',
    'get_content_placement_prompt',
    'TERMINAL_SECTION_SYSTEM',
    'get_terminal_section_prompt',
    'get_content_quality_system',
    'get_content_quality_prompt',
    'INFORMATION_EXTRACTION_SYSTEM',
    'get_information_extraction_prompt',
    'TOC_PLACEMENT_SYSTEM',
    'get_toc_placement_prompt',
    'CONTENT_INTENT_SYSTEM',
    'get_content_intent_prompt',
    'CHUNK_RANKING_SYSTEM',
    'get_chunk_ranking_prompt',
    
    # Helpers
    'format_materials_with_content',
    'format_chunks_for_reference',
    'get_content_type_template',
    'format_microsoft_elements'
]
