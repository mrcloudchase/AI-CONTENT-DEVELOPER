"""
Base class for content generation processors using LLM-native approach
"""
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

from ..models import DocumentChunk, Config, ContentDecision
from ..processors.llm_native_processor import LLMNativeProcessor
from ..utils import write, mkdir

logger = logging.getLogger(__name__)


class BaseContentProcessor(LLMNativeProcessor):
    """Base class for CREATE and UPDATE processors using LLM-native approach"""
    
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
    
    def _check_for_gaps(self, action: ContentDecision, materials_content: Dict[str, str],
                        existing_content: str = None, config = None) -> Dict:
        """Check if we have the required materials for this action
        
        Args:
            action: The action dictionary with update details
            materials_content: Dictionary of material sources and their content
            existing_content: The current content of the file being updated (optional)
            config: Configuration object with content goal and audience info
        """
        gaps = []
        
        # Check if materials are empty
        if not materials_content:
            gaps.append("No materials provided")
            return {
                'has_gaps': True,
                'missing_info': gaps,
                'requested_file': action.filename or action.target_file or 'Unknown',
                'suggestions': ["Please provide relevant documentation materials"]
            }
        
        # For UPDATE actions with existing content, do comprehensive sufficiency check
        if existing_content and action.action == 'UPDATE' and config:
            sufficiency_result = self._perform_comprehensive_sufficiency_check(
                action, materials_content, existing_content, config
            )
            
            return {
                'has_gaps': not sufficiency_result.get('has_sufficient_information', False),
                'missing_info': sufficiency_result.get('insufficient_areas', []),
                'requested_file': action.filename or action.target_file or 'Unknown',
                'suggestions': sufficiency_result.get('suggestions', []),
                'coverage_percentage': sufficiency_result.get('coverage_percentage', 0)
            }
        
        # Fallback to simple check for other cases
        if materials_content and (action.reason or action.rationale):
            reason_text = action.reason or action.rationale or ''
            sufficiency_check = self.extract_key_information(
                content=self._format_materials_for_extraction(materials_content),
                extraction_purpose=f"Check if materials contain sufficient information for: {reason_text}",
                operation_name="Material Sufficiency Check"
            )
            
            # Display thinking if available
            if self.console_display and 'thinking' in sufficiency_check:
                self.console_display.show_thinking(sufficiency_check['thinking'], "🤔 AI Thinking - Material Sufficiency Check")
            
            if sufficiency_check.get('insufficient_areas'):
                gaps.extend(sufficiency_check['insufficient_areas'])
        
        return {
            'has_gaps': len(gaps) > 0,
            'missing_info': gaps,
            'requested_file': action.filename or action.target_file or 'Unknown'
        }
    
    def _perform_comprehensive_sufficiency_check(self, action: ContentDecision, materials_content: Dict[str, str],
                                               existing_content: str, config) -> Dict:
        """Perform comprehensive sufficiency check comparing materials with existing content"""
        
        # Create the prompt inline instead of importing
        prompt = f"""Analyze if the provided materials contain sufficient information to update the existing document.

GOAL: {config.content_goal}
TARGET FILE: {action.filename or action.target_file or 'Unknown'}
UPDATE REASON: {action.reason or action.rationale or 'No reason provided'}

EXISTING DOCUMENT:
{existing_content[:2000]}...

AVAILABLE MATERIALS:
{self._format_materials_clearly(materials_content)}

Determine if materials provide enough NEW information to fulfill the update request.
Focus on: what's already in the document vs. what materials provide that's new and relevant."""

        # Use specific schema for comprehensive sufficiency check
        expected_format = {
            "thinking": [
                "First, I'll analyze what content already exists in the document",
                "Next, I'll review what new information the materials provide",
                "Then, I'll assess if materials cover all update requirements",
                "Finally, I'll determine if this is sufficient for a quality update"
            ],
            "has_sufficient_information": True,
            "coverage_percentage": 85,
            "insufficient_areas": [],
            "suggestions": [],
            "confidence": 90
        }
        
        result = self.extract_key_information(
            content=prompt,
            extraction_purpose="Material sufficiency analysis for content update",
            operation_name="Material Sufficiency Check",
            expected_format=expected_format
        )
        
        # Display thinking if available
        if self.console_display and 'thinking' in result:
            self.console_display.show_thinking(result['thinking'], "🤔 AI Thinking - Material Sufficiency Check")
        
        return result
    
    def _format_materials_clearly(self, materials_content: Dict[str, str]) -> str:
        """Format materials content clearly for the sufficiency check"""
        if not materials_content:
            return "No materials provided"
        
        formatted_parts = []
        for i, (source, content) in enumerate(materials_content.items(), 1):
            # Truncate very long content for the check
            display_content = content
            if len(content) > 5000:
                display_content = content[:5000] + f"\n\n[... truncated. Full content contains {len(content)} characters ...]"
            
            formatted_parts.append(f"""
=== MATERIAL {i}: {source} ===
{display_content}
""")
        
        return "\n".join(formatted_parts)
    
    def _format_materials_for_extraction(self, materials_content: Dict[str, str]) -> str:
        """Format materials for simple extraction (backward compatibility)"""
        # Use the clearer formatting instead of str(dict)
        return self._format_materials_clearly(materials_content)
    
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
    
    def _create_gap_report(self, action: ContentDecision, materials_content: Dict[str, str],
                          relevant_chunks: Optional[Dict], error: str = None,
                          additional_info: List[str] = None) -> Dict:
        """Create a comprehensive gap report for missing information"""
        gap_report = {
            'requested_action': action.action or 'Unknown',
            'requested_file': action.filename or action.target_file or 'Unknown',
            'content_type': action.content_type or 'Unknown',
            'materials_provided': list(materials_content.keys()) if materials_content else [],
            'has_relevant_chunks': bool(relevant_chunks),
            'error': error,
            'missing_information': [],
            'recommendations': []
        }
        
        # Use LLM to analyze what's missing
        if materials_content:
            gap_analysis = self.extract_key_information(
                content=f"Action requested: {action}\nMaterials available: {list(materials_content.keys())}",
                extraction_purpose="Identify what information is missing to fulfill this documentation request",
                operation_name="Gap Analysis"
            )
            
            # Display thinking if available
            if self.console_display and 'thinking' in gap_analysis:
                self.console_display.show_thinking(gap_analysis['thinking'], "🤔 AI Thinking - Gap Analysis")
            
            if gap_analysis.get('missing_items'):
                gap_report['missing_information'].extend(gap_analysis['missing_items'])
            if gap_analysis.get('recommendations'):
                gap_report['recommendations'].extend(gap_analysis['recommendations'])
        
        # Add any additional info provided
        if additional_info:
            gap_report['missing_information'].extend(additional_info)
        
        return gap_report 