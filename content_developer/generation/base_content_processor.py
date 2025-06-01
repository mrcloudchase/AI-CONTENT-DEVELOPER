"""
Base class for content generation processors
"""
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ..models import DocumentChunk
from ..processors.smart_processor import SmartProcessor
from ..utils import write, mkdir


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