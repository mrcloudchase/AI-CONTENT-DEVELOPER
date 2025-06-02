"""
Directory detection processor
"""
from pathlib import Path
from typing import Dict, List
import logging

from ..prompts import get_directory_selection_prompt, DIRECTORY_SELECTION_SYSTEM
from .smart_processor import SmartProcessor

logger = logging.getLogger(__name__)


class DirectoryDetector(SmartProcessor):
    """Detect appropriate working directory for content development"""
    
    def _process(self, repo_path: Path, repo_structure: str, summaries: List[Dict]) -> Dict:
        """Process repository structure and materials to select working directory"""
        materials_info = self._format_materials(summaries) if summaries else "No materials"
        
        prompt = get_directory_selection_prompt(
            self.config, 
            str(repo_path), 
            repo_structure, 
            materials_info
        )
        system = DIRECTORY_SELECTION_SYSTEM
        
        result = self.llm_call(system, prompt, operation_name="Working Directory Selection")
        
        # Validate the selected directory
        result = self._validate_directory_selection(result, repo_path)
        
        self.save_interaction(
            prompt, 
            result, 
            "working_directory", 
            "./llm_outputs/decisions/working_directory"
        )
        
        return result
    
    def _validate_directory_selection(self, result: Dict, repo_path: Path) -> Dict:
        """Validate and potentially correct directory selection"""
        working_dir = result.get('working_directory', '')
        
        # Check if a file was selected instead of a directory
        if working_dir.endswith('.md') or working_dir.endswith('.yml') or working_dir.endswith('.json'):
            logger.warning(f"LLM selected a file instead of directory: {working_dir}")
            # Get the parent directory
            working_dir = '/'.join(working_dir.split('/')[:-1]) if '/' in working_dir else ''
            if working_dir:
                logger.info(f"Correcting to parent directory: {working_dir}")
                result['working_directory'] = working_dir
                result['justification'] = f"Corrected from file to parent directory. {result.get('justification', '')}"
                result['confidence'] = result.get('confidence', 0.5) * 0.8  # Reduce confidence
            else:
                # Mark as failed - will trigger interactive selection
                result['working_directory'] = ''
                result['confidence'] = 0.0
                result['error'] = 'LLM selected a file but could not determine parent directory'
        
        # Check if it's a media/asset directory
        if self._is_media_directory(working_dir):
            logger.warning(f"LLM selected media directory: {working_dir}")
            
            # Try to find a better parent directory
            corrected_dir = self._find_content_directory(working_dir)
            if corrected_dir and corrected_dir != 'articles':  # Don't use generic fallback
                logger.info(f"Correcting to content directory: {corrected_dir}")
                result['working_directory'] = corrected_dir
                result['justification'] = f"Corrected from media directory to content directory. {result.get('justification', '')}"
                result['confidence'] = result.get('confidence', 0.5) * 0.8  # Reduce confidence
            else:
                # Mark as failed - will trigger interactive selection
                result['working_directory'] = ''
                result['confidence'] = 0.0
                result['error'] = 'LLM selected a media directory with no suitable parent'
        
        # Additional validation: check if directory actually exists
        if result.get('working_directory'):
            full_path = repo_path / result['working_directory']
            if not full_path.exists():
                logger.warning(f"Selected directory does not exist: {full_path}")
                # Mark as failed - will trigger interactive selection
                result['working_directory'] = ''
                result['confidence'] = 0.0
                result['error'] = f'Selected directory does not exist: {result.get("working_directory")}'
        
        return result
    
    def _is_media_directory(self, directory: str) -> bool:
        """Check if directory is likely a media/assets directory"""
        media_indicators = ['media', 'assets', 'images', 'img', 'figures', 'diagrams', 'screenshots']
        dir_parts = directory.lower().split('/')
        
        return any(indicator in dir_parts for indicator in media_indicators)
    
    def _find_content_directory(self, media_dir: str) -> str:
        """Find a suitable content directory from a media directory path"""
        # Remove media-related segments from the path
        parts = media_dir.split('/')
        media_indicators = ['media', 'assets', 'images', 'img', 'figures', 'diagrams', 'screenshots']
        
        # Filter out media segments
        content_parts = [part for part in parts if part.lower() not in media_indicators]
        
        # Return the cleaned path if it has meaningful segments
        if content_parts:
            # For cases like "articles/aks/media/concepts-network", we want "articles/aks"
            # not "articles/aks/concepts-network" since concept files are at the aks level
            if len(content_parts) >= 2 and content_parts[-1].startswith('concepts'):
                # Drop the concepts part and use the parent directory
                return '/'.join(content_parts[:-1])
            return '/'.join(content_parts)
        
        return ''  # Return empty string instead of generic fallback
    
    def _format_materials(self, summaries: List[Dict]) -> str:
        """Format material summaries for prompt"""
        return "\n".join([
            f"• {s.get('source', 'Unknown')}: {s.get('main_topic', 'N/A')}\n"
            f"  Summary: {s.get('summary', 'N/A')}\n"
            f"  Technologies: {', '.join(s.get('technologies', []) or [])}\n"
            f"  Key Concepts: {', '.join(s.get('key_concepts', []) or [])}\n"
            f"  Products: {', '.join(s.get('microsoft_products', []) or [])}"
            for s in summaries
        ]) 