"""
Core utilities for AI Content Developer
"""
import hashlib
from functools import wraps
from typing import Callable
import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Hash generation for string content
get_hash = lambda content: hashlib.sha256(content.encode('utf-8')).hexdigest()

def error_handler(func: Callable) -> Callable:
    """
    Decorator to handle errors gracefully
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that returns None on error
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return None
    return wrapper

def extract_from_markdown_block(content: str) -> str:
    """Extract content from markdown code blocks.
    
    Handles various formats:
    - ```markdown...```
    - ````markdown...````
    - ```...``` (generic code block)
    
    Returns the content without the code block markers.
    """
    if not content:
        return content
    
    # Pattern for markdown blocks with optional language specifier
    # Handles both ``` and ```` markers
    patterns = [
        (r'^````markdown\s*\n(.*?)\n````$', re.DOTALL),
        (r'^```markdown\s*\n(.*?)\n```$', re.DOTALL),
        (r'^````\s*\n(.*?)\n````$', re.DOTALL),
        (r'^```\s*\n(.*?)\n```$', re.DOTALL),
    ]
    
    content = content.strip()
    
    for pattern, flags in patterns:
        match = re.match(pattern, content, flags)
        if match:
            return match.group(1).strip()
    
    # If no code block markers found, return as-is
    return content 