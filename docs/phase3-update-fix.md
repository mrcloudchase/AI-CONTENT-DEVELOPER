# Phase 3 Update Error Fix

## Problem
When running Phase 3 content generation with UPDATE actions, the system failed with:
```
ERROR Phase 3 failed: get_update_content_prompt() missing 3 required positional arguments: 'chunk_context', 'content_type_info', and 'content_standards'
```

## Root Cause
The `ContentGenerationProcessor` in `processors/generation.py` was calling `get_update_prompt()` with only 4 parameters:
```python
prompt = get_update_prompt(decision, existing_content, formatted_materials, config)
```

But the function signature requires 7 parameters:
```python
def get_update_content_prompt(
    config, action: Dict, existing_content: str, material_context: str,
    chunk_context: str, content_type_info: Dict, content_standards: Dict) -> str:
```

## Solution
Updated the `_update_content` method in `ContentGenerationProcessor` to:
1. Extract content type info from the existing document's frontmatter
2. Build proper chunk context (empty for now)
3. Provide content standards structure
4. Convert ContentDecision to action dict format
5. Pass all 7 required parameters

## Key Changes
- Added extraction of `ms.topic` from frontmatter to determine content type
- Created proper `content_type_info` dictionary
- Added empty `content_standards` structure (can be loaded from file later)
- Converted `ContentDecision` object to `action` dict expected by prompt
- Updated result extraction to handle `updated_document` field

## Result
Phase 3 UPDATE actions now work correctly with all required parameters passed to the prompt function. 