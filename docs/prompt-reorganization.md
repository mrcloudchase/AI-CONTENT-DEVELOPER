# Prompt Reorganization Documentation

## Overview

All prompts in the AI Content Developer have been reorganized into individual files for better maintainability and clarity. Each prompt now exists in its own file under a phase-based directory structure.

## New Directory Structure

```
content_developer/prompts/
├── phase1/                    # Repository Analysis
│   ├── material_summary.py    # Material analysis prompt
│   └── directory_selection.py # Directory selection prompt
│
├── phase2/                    # Content Strategy
│   └── unified_strategy.py    # Strategy generation prompt
│
├── phase3/                    # Content Generation
│   ├── create_content.py      # New content creation prompt
│   ├── update_content.py      # Content update prompt
│   └── material_sufficiency.py # Sufficiency check prompt
│
├── phase4/                    # TOC Management
│   └── toc_update.py          # TOC update prompt
│
├── supporting/                # Supporting prompts
│   ├── content_placement.py   # Content placement analysis
│   ├── terminal_section.py    # Terminal section detection
│   ├── content_quality.py     # Quality evaluation
│   ├── information_extraction.py # Flexible info extraction
│   └── chunk_ranking.py       # Chunk relevance ranking
│
├── helpers.py                 # Utility functions (unchanged)
├── schemas.py                 # JSON schemas (unchanged)
└── __init__.py               # Main imports
```

## Backward Compatibility

The original files (`material.py`, `directory.py`, `strategy.py`, `generation.py`, `toc.py`, `llm_native.py`) have been converted to import aggregators. They now simply import from the new locations and re-export the same functions/constants, ensuring all existing code continues to work without modification.

## Benefits

1. **Clear Organization**: Prompts are organized by processing phase
2. **Easy Navigation**: Each prompt has its own file with a descriptive name
3. **Maintainability**: Changes to one prompt don't affect others
4. **Scalability**: Easy to add new prompts in the appropriate phase
5. **Backward Compatibility**: Existing imports continue to work
6. **Testing**: Individual prompt files can be tested in isolation

## Usage

### Importing Prompts

You can import prompts in several ways:

```python
# Option 1: Import from main prompts module (recommended)
from content_developer.prompts import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)

# Option 2: Import from phase-specific module
from content_developer.prompts.phase1 import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)

# Option 3: Import from specific file
from content_developer.prompts.phase1.material_summary import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)

# Option 4: Import from backward-compatibility module (legacy)
from content_developer.prompts.material import (
    get_material_summary_prompt,
    MATERIAL_SUMMARY_SYSTEM
)
```

## Adding New Prompts

To add a new prompt:

1. Determine which phase it belongs to (or if it's a supporting prompt)
2. Create a new `.py` file in the appropriate directory
3. Define the prompt function and system constant
4. Add imports to the phase's `__init__.py`
5. Update the main `__init__.py` to export the new prompt

Example:
```python
# content_developer/prompts/phase3/validation.py
"""
Validation Prompt - Phase 3: Content Generation
Validates generated content against standards
"""

def get_validation_prompt(...) -> str:
    """Get the prompt for content validation"""
    # Implementation

VALIDATION_SYSTEM = """You are an expert..."""
```

## File Naming Conventions

- Use lowercase with underscores
- Name should reflect the prompt's purpose
- Examples:
  - `material_summary.py` - For summarizing materials
  - `content_placement.py` - For determining content placement
  - `terminal_section.py` - For identifying terminal sections 