"""
Supporting prompts for various documentation tasks
"""
from .content_placement import (
    get_content_placement_prompt,
    CONTENT_PLACEMENT_SYSTEM
)
from .terminal_section import (
    get_terminal_section_prompt,
    TERMINAL_SECTION_SYSTEM
)
from .content_quality import (
    get_content_quality_prompt,
    get_content_quality_system
)
from .information_extraction import (
    get_information_extraction_prompt,
    INFORMATION_EXTRACTION_SYSTEM
)
from .chunk_ranking import (
    get_chunk_ranking_prompt,
    CHUNK_RANKING_SYSTEM
)

__all__ = [
    'get_content_placement_prompt',
    'CONTENT_PLACEMENT_SYSTEM',
    'get_terminal_section_prompt',
    'TERMINAL_SECTION_SYSTEM',
    'get_content_quality_prompt',
    'get_content_quality_system',
    'get_information_extraction_prompt',
    'INFORMATION_EXTRACTION_SYSTEM',
    'get_chunk_ranking_prompt',
    'CHUNK_RANKING_SYSTEM'
] 