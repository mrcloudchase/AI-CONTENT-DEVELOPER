"""
Base class for content generation processors
"""
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

from ..models import DocumentChunk
from ..processors.smart_processor import SmartProcessor
from ..utils import write, mkdir

logger = logging.getLogger(__name__)


class BaseContentProcessor(SmartProcessor):
    """Base class for CREATE and UPDATE processors with shared functionality"""
    
    @abstractmethod
    def _process_action(self, action: Dict, materials: List[Dict], 
                       materials_content: Dict[str, str], chunks: List[DocumentChunk],
                       repo_name: str, working_directory: str,
                       relevant_chunks: Dict[str, DocumentChunk],
                       chunks_with_context: Dict[str, Dict],
                       working_dir_path: Path) -> Dict:
        """Process a single action - must be implemented by subclasses"""
        pass
    
    def process(self, action: Dict, materials: List[Dict], 
               materials_content: Dict[str, str], chunks: List[DocumentChunk],
               working_dir_path: Path, repo_name: str, working_directory: str,
               relevant_chunks: Optional[Dict[str, DocumentChunk]] = None,
               chunks_with_context: Optional[Dict[str, Dict]] = None) -> Dict:
        """Public interface for processing an action"""
        return self._process_action(
            action, materials, materials_content, chunks,
            repo_name, working_directory,
            relevant_chunks or {},
            chunks_with_context or {},
            working_dir_path
        )
    
    def _create_error_result(self, action: Dict, error_message: str) -> Dict:
        """Create a standardized error result"""
        return {
            'action': action,
            'success': False,
            'error': error_message
        }
    
    def _create_gap_result(self, action: Dict, gap_report: Dict) -> Dict:
        """Create a result with gap analysis"""
        return {
            'action': action,
            'success': False,
            'gap_report': gap_report
        }
    
    def _check_for_gaps(self, action: Dict, materials_content: Dict[str, str]) -> Dict:
        """Check if we have the required materials for this action"""
        gaps = []
        
        # Check if materials are empty
        if not materials_content:
            gaps.append("No materials provided")
        
        # Check for specific content types mentioned in action
        if reason := action.get('reason', ''):
            if 'tutorial' in reason.lower() and not self._has_tutorial_content(materials_content):
                gaps.append("No tutorial-style content in materials")
            if 'reference' in reason.lower() and not self._has_reference_content(materials_content):
                gaps.append("No reference documentation in materials")
        
        return {
            'has_gaps': len(gaps) > 0,
            'missing_info': gaps,
            'requested_file': action.get('filename', 'Unknown')
        }
    
    def _save_preview(self, content: str, filename: str, repo_name: str, 
                     working_directory: str, action_type: str) -> str:
        """Save content preview and return path"""
        preview_dir = Path("./llm_outputs/preview") / repo_name / working_directory / action_type
        mkdir(preview_dir)
        
        preview_path = preview_dir / filename
        write(preview_path, content)
        
        return str(preview_path)
    
    def _build_material_context(self, materials: List[Dict], 
                               materials_content: Dict[str, str], 
                               action: Dict) -> str:
        """Build material context for prompt"""
        if not materials_content:
            return "No materials available"
        
        context_parts = []
        
        for material in materials:
            source = material.get('source', 'Unknown')
            if source in materials_content:
                content = materials_content[source]
                # Truncate very long content
                if len(content) > 10000:
                    content = content[:10000] + "\n... [content truncated]"
                
                context_parts.append(f"=== Material: {source} ===")
                context_parts.append(f"Topic: {material.get('main_topic', 'N/A')}")
                context_parts.append(f"Type: {material.get('document_type', 'N/A')}")
                context_parts.append(f"\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_chunk_context(self, relevant_chunks: Dict[str, DocumentChunk],
                            chunks_with_context: Dict[str, Dict]) -> str:
        """Build context from relevant chunks"""
        if not relevant_chunks:
            return "No existing documentation context available"
        
        context_parts = []
        
        for chunk_id, chunk in relevant_chunks.items():
            context_parts.append(f"\n--- Existing Documentation ---")
            context_parts.append(f"File: {chunk.file_path}")
            context_parts.append(f"Section: {' > '.join(chunk.heading_path) if chunk.heading_path else 'Main'}")
            
            # Add context if available
            if chunk_id in chunks_with_context:
                context_info = chunks_with_context[chunk_id]
                if context_info.get('prev_content'):
                    context_parts.append(f"[Previous: ...{context_info['prev_content']}]")
                
                context_parts.append(f"\n{chunk.content}\n")
                
                if context_info.get('next_content'):
                    context_parts.append(f"[Next: {context_info['next_content']}...]")
            else:
                context_parts.append(f"\n{chunk.content}\n")
        
        return "\n".join(context_parts)
    
    def _has_tutorial_content(self, materials_content: Dict[str, str]) -> bool:
        """Check if materials contain tutorial-style content"""
        tutorial_keywords = ['step-by-step', 'tutorial', 'walkthrough', 'example', 'hands-on']
        content_text = ' '.join(materials_content.values()).lower()
        return any(keyword in content_text for keyword in tutorial_keywords)
    
    def _has_reference_content(self, materials_content: Dict[str, str]) -> bool:
        """Check if materials contain reference documentation"""
        reference_keywords = ['api', 'reference', 'parameters', 'methods', 'properties']
        content_text = ' '.join(materials_content.values()).lower()
        return any(keyword in content_text for keyword in reference_keywords)
    
    def _load_content_standards(self) -> Dict:
        """Load content standards from JSON file"""
        standards_path = Path('content_standards.json')
        if standards_path.exists():
            try:
                with open(standards_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load content standards: {e}")
        return {}
    
    def _get_content_type_info(self, standards: Dict, content_type: str) -> Dict:
        """Get content type information from standards"""
        if not standards:
            return {'name': content_type}
        
        content_types = standards.get('contentTypes', [])
        for ct in content_types:
            if ct.get('name') == content_type:
                return ct
        
        return {'name': content_type}
    
    def _create_gap_report(self, action: Dict, materials_content: Dict[str, str],
                          relevant_chunks: Optional[Dict], error: str = None,
                          additional_info: List[str] = None) -> Dict:
        """Create a comprehensive gap report for missing information"""
        gap_report = {
            'requested_action': action.get('action', 'Unknown'),
            'requested_file': action.get('filename', 'Unknown'),
            'content_type': action.get('content_type', 'Unknown'),
            'materials_provided': list(materials_content.keys()) if materials_content else [],
            'has_relevant_chunks': bool(relevant_chunks),
            'error': error,
            'missing_information': [],
            'recommendations': []
        }
        
        # Check what's missing based on content type
        content_type = action.get('content_type', '')
        content_brief = action.get('content_brief', {})
        
        # Check for missing examples
        if content_brief.get('code_examples_needed'):
            has_examples = any('```' in content for content in materials_content.values())
            if not has_examples:
                gap_report['missing_information'].append("Code examples or configurations")
                gap_report['recommendations'].append("Provide material with code samples")
        
        # Check for missing prerequisites
        if content_brief.get('prerequisites_to_state'):
            gap_report['missing_information'].append("Clear prerequisite information")
            gap_report['recommendations'].append("Include setup or requirement details")
        
        # Add any additional info provided
        if additional_info:
            gap_report['missing_information'].extend(additional_info)
        
        return gap_report
    
    def _is_terminal_section(self, section_name: str, content_type_info: Dict) -> bool:
        """Check if a section is terminal (must be last) for the given content type"""
        terminal_sections = content_type_info.get('terminalSections', [])
        
        # Normalize section name for comparison
        normalized_section = section_name.strip().lower()
        
        for terminal in terminal_sections:
            if normalized_section == terminal.lower():
                return True
        
        # Also check common terminal sections and variations
        common_terminals = [
            'next steps', 'next step', 'related content', 'see also', 
            'conclusion', 'references', 'related documentation',
            'additional resources', 'further reading', 'learn more',
            'additional information'
        ]
        
        # Check exact matches
        if normalized_section in common_terminals:
            return True
            
        # Check if section starts with "related" (covers many variations)
        if normalized_section.startswith('related'):
            return True
            
        # Check if section contains "next step" (covers variations)
        if 'next step' in normalized_section:
            return True
            
        # Check for "next" patterns that indicate moving forward
        # Must be more than just containing "next" - needs context
        next_patterns = [
            "what's next", "whats next", "what next",
            "next actions", "next tasks", "up next"
        ]
        if any(pattern in normalized_section for pattern in next_patterns):
            return True
            
        # Check if it starts with "next" (but not "next generation" etc.)
        if normalized_section.startswith('next '):
            return True
            
        # Check for sections that are clearly navigational
        navigation_keywords = ['see also', 'learn more', 'additional', 'further', 'more info']
        if any(keyword in normalized_section for keyword in navigation_keywords):
            return True
            
        return False
    
    def _find_section_position(self, section_name: str, content_type_info: Dict) -> int:
        """Find the position value for a section in the content type's section order"""
        section_order = content_type_info.get('sectionOrder', [])
        normalized_name = section_name.strip().lower()
        
        for section in section_order:
            # Check primary name
            if section['name'].lower() == normalized_name:
                return section['position']
            
            # Check alternate names
            alternates = section.get('alternateNames', [])
            if any(alt.lower() == normalized_name for alt in alternates):
                return section['position']
        
        # Default position for unknown sections (before terminal)
        return 50
    
    def _validate_section_placement(self, existing_sections: List[str], new_section: str, 
                                   insertion_point: str, content_type_info: Dict) -> Dict:
        """Validate if a new section can be placed at the specified insertion point"""
        validation = {
            'valid': True,
            'reason': '',
            'suggested_position': insertion_point
        }
        
        # Check if insertion point is after a terminal section
        if self._is_terminal_section(insertion_point, content_type_info):
            validation['valid'] = False
            validation['reason'] = f"Cannot add content after terminal section '{insertion_point}'"
            
            # Find last non-terminal section
            for i in range(len(existing_sections) - 1, -1, -1):
                if not self._is_terminal_section(existing_sections[i], content_type_info):
                    validation['suggested_position'] = existing_sections[i]
                    break
            
            return validation
        
        # Check section order rules
        new_section_pos = self._find_section_position(new_section, content_type_info)
        insertion_pos = self._find_section_position(insertion_point, content_type_info)
        
        # Find next section position
        insertion_index = existing_sections.index(insertion_point) if insertion_point in existing_sections else -1
        if insertion_index >= 0 and insertion_index < len(existing_sections) - 1:
            next_section = existing_sections[insertion_index + 1]
            next_pos = self._find_section_position(next_section, content_type_info)
            
            # Validate ordering
            if new_section_pos >= next_pos and next_pos == 99:  # 99 is terminal position
                validation['valid'] = False
                validation['reason'] = f"Section '{new_section}' would be placed after terminal section"
        
        return validation
    
    def _extract_sections_from_content(self, content: str) -> List[str]:
        """Extract section headings from markdown content"""
        import re
        
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            # Match H2 headings (##)
            if match := re.match(r'^##\s+(.+)$', line.strip()):
                sections.append(match.group(1).strip())
        
        return sections 