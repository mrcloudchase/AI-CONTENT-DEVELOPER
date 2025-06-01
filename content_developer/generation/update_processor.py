"""
Update processor for modifying existing content
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..models import DocumentChunk
from ..utils import read, write, mkdir, extract_from_markdown_block
from ..prompts import get_update_content_prompt, UPDATE_CONTENT_SYSTEM
from .base_content_processor import BaseContentProcessor

logger = logging.getLogger(__name__)


class UpdateContentProcessor(BaseContentProcessor):
    """Process UPDATE actions from content strategy"""
    
    def _process(self, action: Dict, materials: List[Dict], 
                       materials_content: Dict[str, str], chunks: List[DocumentChunk],
                       working_dir_path: Path, repo_name: str, working_directory: str,
                       relevant_chunks: Dict[str, DocumentChunk] = None,
                       chunks_with_context: Dict[str, Dict] = None) -> Dict:
        """Process a single UPDATE action"""
        filename = action.get('filename', '')
        
        # Load existing file content
        file_path = working_dir_path / filename
        if not file_path.exists():
            return self._create_error_result(action, f"File not found: {filename}")
        
        # Read existing content
        existing_content = read(file_path)
        
        # Check for missing information
        gap_report = self._check_for_gaps(action, materials_content)
        if gap_report['has_gaps']:
            return self._create_gap_result(action, gap_report)
        
        # Generate updated content
        updated_content = self._update_content(
            action, existing_content, materials, materials_content, 
            relevant_chunks, chunks_with_context
        )
        
        if updated_content and updated_content != existing_content:
            # Save preview
            preview_path = self._save_update_preview(
                updated_content, filename, repo_name, working_directory
            )
            
            return {
                'action': action,
                'success': True,
                'updated_content': updated_content,
                'preview_path': preview_path
            }
        else:
            return self._create_error_result(action, "Failed to update content")
    
    def _update_content(self, action: Dict, existing_content: str, 
                       materials: List[Dict], materials_content: Dict[str, str],
                       relevant_chunks: Dict[str, DocumentChunk],
                       chunks_with_context: Dict[str, Dict]) -> Optional[str]:
        """Generate updated content for the file"""
        # Build context from relevant chunks
        chunk_context = self._build_chunk_context(relevant_chunks, chunks_with_context)
        
        # Build material context
        material_context = self._build_material_context(materials, materials_content, action)
        
        # Create update prompt
        messages = [
            {
                "role": "system",
                "content": UPDATE_CONTENT_SYSTEM
            },
            {
                "role": "user",
                "content": get_update_content_prompt(
                    action, existing_content, material_context, chunk_context
                )
            }
        ]
        
        try:
            result = self._call_llm(messages, model="gpt-4o", response_format="json_object")
            
            # Save interaction for debugging
            self.save_interaction(
                messages[1]['content'], 
                result, 
                f"update_{action.get('filename', 'unknown')}", 
                "./llm_outputs/content_generation/update"
            )
            
            # Apply the changes to the existing content
            updated_content = self._apply_changes(existing_content, result.get('changes', []))
            
            return updated_content
            
        except Exception as e:
            logger.error(f"Failed to generate updated content: {e}")
            return None
    
    def _apply_changes(self, original_content: str, changes: List[Dict]) -> str:
        """Apply the specified changes to the original content"""
        if not changes:
            logger.warning("No changes provided by LLM")
            return original_content
        
        updated_content = original_content
        
        # Sort changes by action type to handle adds last
        sorted_changes = sorted(changes, key=lambda x: 0 if x.get('action') != 'add' else 1)
        
        for change in sorted_changes:
            action = change.get('action', '')
            
            if action == 'replace':
                original_text = change.get('original', '')
                updated_text = change.get('updated', '')
                
                if original_text and original_text in updated_content:
                    updated_content = updated_content.replace(original_text, updated_text)
                    logger.info(f"Replaced content in section: {change.get('section', 'Unknown')}")
                else:
                    logger.warning(f"Could not find original text to replace in section: {change.get('section', 'Unknown')}")
            
            elif action == 'modify':
                # Similar to replace but with more context
                original_text = change.get('original', '')
                updated_text = change.get('updated', '')
                
                if original_text and original_text in updated_content:
                    updated_content = updated_content.replace(original_text, updated_text)
                    logger.info(f"Modified content in section: {change.get('section', 'Unknown')}")
                else:
                    logger.warning(f"Could not find original text to modify in section: {change.get('section', 'Unknown')}")
            
            elif action == 'add':
                # For add actions, we need to find the right place to insert
                section = change.get('section', '')
                new_content = change.get('updated', '')
                
                # Try to find the section and add content after it
                if section and new_content:
                    updated_content = self._insert_content_after_section(
                        updated_content, section, new_content
                    )
                    logger.info(f"Added new content to section: {section}")
        
        return updated_content
    
    def _insert_content_after_section(self, content: str, section: str, new_content: str) -> str:
        """Insert new content after a specific section"""
        lines = content.split('\n')
        
        # Find the section
        section_index = -1
        for i, line in enumerate(lines):
            if section.lower() in line.lower() and line.strip().startswith('#'):
                section_index = i
                break
        
        if section_index == -1:
            # If section not found, add at the end
            logger.warning(f"Section '{section}' not found, adding content at the end")
            return content + '\n\n' + new_content
        
        # Find the next section at the same level or higher
        section_level = len(lines[section_index].split()[0])  # Count # characters
        insert_index = len(lines)  # Default to end of file
        
        for i in range(section_index + 1, len(lines)):
            if lines[i].strip().startswith('#'):
                level = len(lines[i].split()[0])
                if level <= section_level:
                    insert_index = i
                    break
        
        # Insert the new content
        lines.insert(insert_index, new_content)
        if insert_index < len(lines) - 1:
            lines.insert(insert_index, '')  # Add blank line before next section
        
        return '\n'.join(lines)
    
    def _save_update_preview(self, content: str, filename: str, 
                            repo_name: str, working_directory: str) -> str:
        """Save updated content preview"""
        preview_dir = Path("./llm_outputs/preview/updates")
        mkdir(preview_dir)
        
        preview_path = preview_dir / filename
        write(preview_path, content)
        
        return str(preview_path) 