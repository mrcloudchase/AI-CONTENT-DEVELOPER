"""
Directory detection processor using LLM-native approach
"""
from pathlib import Path
from typing import Dict, List
import logging

from ..prompts import get_directory_selection_prompt, DIRECTORY_SELECTION_SYSTEM
from .llm_native_processor import LLMNativeProcessor

logger = logging.getLogger(__name__)


class DirectoryDetector(LLMNativeProcessor):
    """Detect appropriate working directory for content development using LLM intelligence"""
    
    def _process(self, repo_path: Path, repo_structure: str, summaries: List[Dict]) -> Dict:
        """Process repository structure and materials to select working directory"""
        materials_info = self._format_materials(summaries) if summaries else "No materials"
        
        # Use LLM to analyze repository structure
        structure_analysis = self.analyze_document_structure(
            repo_structure,
            operation_name="Repository Structure Analysis"
        )
        
        # Get directory recommendation
        prompt = get_directory_selection_prompt(
            self.config, 
            str(repo_path), 
            repo_structure, 
            materials_info
        )
        
        messages = [
            {"role": "system", "content": DIRECTORY_SELECTION_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        result = self._call_llm(
            messages,
            response_format="json_object",
            operation_name="Working Directory Selection"
        )
        
        # Validate the selected directory
        result = self._validate_directory_selection(result, repo_path, structure_analysis)
        
        return result
    
    def _validate_directory_selection(self, result: Dict, repo_path: Path, 
                                    structure_analysis: Dict) -> Dict:
        """Validate directory selection using LLM understanding"""
        working_dir = result.get('working_directory', '')
        
        if not working_dir:
            result['confidence'] = 0.0
            result['error'] = 'No directory selected'
            return result
        
        try:
            # Format structure analysis for string representation
            structure_insights = {
                'sections': structure_analysis.get('sections', []),
                'terminal_sections': structure_analysis.get('terminal_sections', []),
                'content_flow': structure_analysis.get('content_flow', ''),
                'key_topics': structure_analysis.get('key_topics', [])
            }
            
            # Ensure content_flow is a string
            content_flow = structure_insights['content_flow']
            if isinstance(content_flow, list):
                # If LLM returned a list despite instructions, join it
                content_flow_str = ' → '.join(str(item) for item in content_flow)
                logger.warning(f"content_flow was a list, converted to string: {content_flow_str}")
            else:
                content_flow_str = str(content_flow)
            
            # Create a safe string representation
            structure_summary = (
                f"Sections found: {len(structure_insights['sections'])}, "
                f"Terminal sections: {len(structure_insights['terminal_sections'])}, "
                f"Flow: {content_flow_str[:100]}..., "
                f"Topics: {', '.join(str(t) for t in structure_insights['key_topics'][:5])}"
            )
            
            # Use LLM to validate the selection
            validation_check = self.extract_key_information(
                content=f"""Selected directory: {working_dir}
Repository structure insights: {structure_summary}
Service area: {self.config.service_area}
Content goal: {self.config.content_goal}

Validate:
1. Is this an appropriate documentation directory (not media/assets)?
2. Does this directory match the service area '{self.config.service_area}'?
3. If not, what would be a better directory for {self.config.service_area} content?""",
                extraction_purpose="Validate directory selection matches service area and is appropriate for documentation",
                operation_name="Directory Validation"
            )
        except Exception as e:
            logger.error(f"Error during directory validation: {e}")
            logger.error(f"Working dir type: {type(working_dir)}, value: {working_dir}")
            logger.error(f"Structure analysis type: {type(structure_analysis)}")
            # Return the original result without validation
            return result
        
        if not validation_check.get('is_valid', True):
            logger.warning(f"Directory validation raised concerns: {validation_check.get('reason', 'Unknown')}")
            
            # Only use alternative if it exists and is clearly better
            if alternative := validation_check.get('suggested_alternative'):
                # Verify the alternative actually exists
                alt_path = repo_path / alternative
                if alt_path.exists():
                    logger.info(f"Using better alternative directory: {alternative}")
                    result['working_directory'] = alternative
                    result['justification'] = f"Improved selection: {validation_check.get('reason', '')}"
                    result['confidence'] = result.get('confidence', 0.5) * 1.1  # Slight confidence boost
                else:
                    logger.warning(f"Suggested alternative doesn't exist: {alternative}")
                    # Keep original selection
            
            # Log any concerns but don't fail if directory is reasonable
            if concerns := validation_check.get('concerns', []):
                for concern in concerns:
                    logger.warning(f"Validation concern: {concern}")
            
            # Only fail if it's truly invalid (e.g., media folder)
            if not validation_check.get('is_documentation_directory', True):
                result['working_directory'] = ''
                result['confidence'] = 0.0
                result['error'] = 'Selected directory is not suitable for documentation'
        
        # Final check: verify directory exists
        if result.get('working_directory'):
            full_path = repo_path / result['working_directory']
            if not full_path.exists():
                logger.warning(f"Selected directory does not exist: {full_path}")
                result['working_directory'] = ''
                result['confidence'] = 0.0
                result['error'] = f'Directory does not exist: {result.get("working_directory")}'
        
        return result
    
    def _format_materials(self, summaries: List[Dict]) -> str:
        """Format material summaries for prompt"""
        formatted_summaries = []
        
        for s in summaries:
            # Safely get list fields, ensuring they are actually lists
            technologies = s.get('technologies', [])
            if not isinstance(technologies, list):
                technologies = [technologies] if technologies else []
                
            key_concepts = s.get('key_concepts', [])
            if not isinstance(key_concepts, list):
                key_concepts = [key_concepts] if key_concepts else []
                
            microsoft_products = s.get('microsoft_products', [])
            if not isinstance(microsoft_products, list):
                microsoft_products = [microsoft_products] if microsoft_products else []
            
            summary_text = (
            f"• {s.get('source', 'Unknown')}: {s.get('main_topic', 'N/A')}\n"
            f"  Summary: {s.get('summary', 'N/A')}\n"
                f"  Technologies: {', '.join(str(t) for t in technologies)}\n"
                f"  Key Concepts: {', '.join(str(k) for k in key_concepts)}\n"
                f"  Products: {', '.join(str(p) for p in microsoft_products)}"
            )
            formatted_summaries.append(summary_text)
            
        return "\n".join(formatted_summaries) 