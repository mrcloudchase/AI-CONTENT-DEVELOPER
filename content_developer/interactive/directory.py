"""
Directory selection confirmation
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .generic_interactive import GenericInteractive
from .selector import InteractiveSelector

logger = logging.getLogger(__name__)


class DirectoryConfirmation(GenericInteractive):
    """Confirm working directory selection"""
    
    def __init__(self, config):
        super().__init__(config, self._format_directory)
    
    def confirm(self, llm_result: Optional[Dict], repo_structure: str, llm_failed: bool = False, error: str = "") -> Dict:
        """Confirm directory selection"""
        result = super().confirm(llm_result, llm_failed, error)
        
        # Ensure result is in dictionary format
        if isinstance(result, dict):
            return result
        
        # Convert string result to dictionary format
        return self._create_directory_result(result)
    
    def _create_directory_result(self, directory_path: str) -> Dict:
        """Create a properly formatted directory result"""
        return {
            "working_directory": directory_path,
            "justification": "Manual selection"
        }
    
    def _format_directory(self, result):
        """Format directory result for display"""
        return f"📁 Selected Directory: {result.get('working_directory', 'Unknown')}\n" \
               f"📝 Reason: {result.get('justification', 'No reason provided')}\n" \
               f"🎯 Confidence: {result.get('confidence', 0):.0%}"
    
    def _manual_selection(self, reason):
        """Manual directory selection"""
        print(f"\n🔧 Manual directory selection ({reason})")
        
        # Extract directories from structure
        dirs = self._extract_directories(self.repo_structure)
        
        # Use interactive selector
        selected = InteractiveSelector.paginated_selection(
            dirs,
            title="Select Working Directory",
            page_size=20
        )
        
        if selected:
            return {"working_directory": selected, "justification": "Manual selection"}
        else:
            raise SystemExit("No directory selected")
    
    def _extract_directories(self, structure: str) -> List[str]:
        """Extract directory paths from structure string"""
        directories = []
        current_path_stack = []
        
        for line in structure.split('\n'):
            if not line.strip():
                continue
            
            directory_info = self._parse_directory_line(line)
            if not directory_info:
                continue
            
            # Update path stack based on indentation
            indent_level, directory_name = directory_info
            current_path_stack = current_path_stack[:indent_level] + [directory_name]
            
            # Add valid directories to list
            if self._is_valid_directory(line, directory_name):
                full_path = '/'.join(current_path_stack)
                directories.append(full_path)
        
        return sorted(directories)
    
    def _parse_directory_line(self, line: str) -> Optional[tuple]:
        """Parse a line to extract indentation level and directory name"""
        # Count indentation level
        stripped_line = line.lstrip()
        indent_spaces = len(line) - len(stripped_line)
        indent_level = indent_spaces // 4
        
        # Extract directory name
        line_parts = stripped_line.split(' ')
        if len(line_parts) < 2:
            return None
        
        directory_name = line_parts[-1].rstrip('/')
        return (indent_level, directory_name)
    
    def _is_valid_directory(self, line: str, directory_name: str) -> bool:
        """Check if a line represents a valid directory"""
        # Skip hidden directories
        if directory_name.startswith('.'):
            return False
        
        # Check if it's a directory indicator
        return (line.rstrip().endswith('/') or 
                '└──' in line or 
                '├──' in line) 