"""
Update processor for modifying existing content
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re
import json

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
        existing_content = read(file_path, limit=None)
        
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
    
    def _extract_content_type_from_document(self, content: str) -> Dict:
        """Extract content type information from document frontmatter"""
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            logger.warning("No frontmatter found in document")
            return {'ms_topic': 'unknown', 'content_type': 'Unknown'}
        
        frontmatter = frontmatter_match.group(1)
        
        # Extract ms.topic
        ms_topic_match = re.search(r'ms\.topic:\s*(\S+)', frontmatter)
        ms_topic = ms_topic_match.group(1) if ms_topic_match else 'unknown'
        
        # Map ms.topic to content type
        ms_topic_to_content_type = {
            'overview': 'Overview',
            'concept-article': 'Concept', 
            'quickstart': 'Quickstart',
            'how-to': 'How-To Guide',
            'tutorial': 'Tutorial'
        }
        
        content_type = ms_topic_to_content_type.get(ms_topic, 'Unknown')
        
        return {
            'ms_topic': ms_topic,
            'content_type': content_type
        }
    
    def _update_content(self, action: Dict, existing_content: str, 
                       materials: List[Dict], materials_content: Dict[str, str],
                       relevant_chunks: Dict[str, DocumentChunk],
                       chunks_with_context: Dict[str, Dict]) -> Optional[str]:
        """Generate updated content for the file"""
        # Extract document content type
        doc_info = self._extract_content_type_from_document(existing_content)
        content_type = doc_info['content_type']
        
        # Load content standards and get content type info
        content_standards = self._load_content_standards()
        content_type_info = self._get_content_type_info(content_standards, content_type)
        
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
                    self.config, action, existing_content, material_context, chunk_context,
                    content_type_info,  # Pass content type info
                    content_standards   # Pass full standards for formatting
                )
            }
        ]
        
        try:
            result = self._call_llm(messages, model=self.config.completion_model, response_format="json_object")
            
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
        
        # Extract content type for validation
        doc_info = self._extract_content_type_from_document(original_content)
        content_standards = self._load_content_standards()
        content_type_info = self._get_content_type_info(content_standards, doc_info['content_type'])
        
        # Extract existing sections for validation
        existing_sections = self._extract_sections_from_content(original_content)
        
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
                
                # Validate section placement
                if section and section in existing_sections:
                    validation = self._validate_section_placement(
                        existing_sections, section, section, content_type_info
                    )
                    
                    if not validation['valid']:
                        logger.warning(f"Invalid placement: {validation['reason']}")
                        if validation['suggested_position'] and validation['suggested_position'] != section:
                            logger.info(f"Placing content after '{validation['suggested_position']}' instead")
                            section = validation['suggested_position']
                        else:
                            logger.error(f"Cannot add content after terminal section '{section}'")
                            continue
                
                # Try to find the section and add content after it
                if section and new_content:
                    updated_content = self._insert_content_after_section(
                        updated_content, section, new_content, content_type_info
                    )
                    logger.info(f"Added new content to section: {section}")
        
        return updated_content
    
    def _insert_content_after_section(self, content: str, section: str, new_content: str, 
                                    content_type_info: Dict) -> str:
        """Insert new content after a specific section with terminal section validation"""
        lines = content.split('\n')
        
        # Find the section
        section_index = -1
        for i, line in enumerate(lines):
            if section.lower() in line.lower() and line.strip().startswith('#'):
                section_index = i
                break
        
        if section_index == -1:
            # If section not found, check if we should add before terminal sections
            logger.warning(f"Section '{section}' not found")
            
            # Find last non-terminal section
            sections = self._extract_sections_from_content(content)
            last_valid_index = -1
            
            for i in range(len(sections) - 1, -1, -1):
                if not self._is_terminal_section(sections[i], content_type_info):
                    # Find this section in the content
                    for j, line in enumerate(lines):
                        if sections[i].lower() in line.lower() and line.strip().startswith('#'):
                            last_valid_index = j
                            break
                    break
            
            if last_valid_index >= 0:
                section_index = last_valid_index
                logger.info(f"Adding content after last non-terminal section")
            else:
                logger.error("Could not find appropriate place to add content")
                return content
        
        # Check if this is a terminal section
        if self._is_terminal_section(section, content_type_info):
            logger.error(f"Cannot add content after terminal section '{section}'")
            return content
        
        # Find the next section at the same level or higher
        section_level = len(lines[section_index].split()[0])  # Count # characters
        insert_index = len(lines)  # Default to end of file
        
        for i in range(section_index + 1, len(lines)):
            if lines[i].strip().startswith('#'):
                level = len(lines[i].split()[0])
                if level <= section_level:
                    insert_index = i
                    break
        
        # Validate that we're not inserting after a terminal section
        if insert_index < len(lines):
            # Check if the next section is terminal
            next_section_match = re.match(r'^#+\s+(.+)$', lines[insert_index].strip())
            if next_section_match:
                next_section = next_section_match.group(1)
                if self._is_terminal_section(next_section, content_type_info):
                    # We're about to insert before a terminal section, which is OK
                    logger.info(f"Inserting content before terminal section '{next_section}'")
        
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