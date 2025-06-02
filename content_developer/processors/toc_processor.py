"""
TOC (Table of Contents) processor for managing TOC.yml entries
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .smart_processor import SmartProcessor
from ..models import DocumentChunk
from ..utils import read, write

logger = logging.getLogger(__name__)


class TOCProcessor(SmartProcessor):
    """Process TOC.yml to ensure all documentation is properly indexed"""
    
    def process(
        self,
        working_directory: Path,
        created_files: List[str],
        updated_files: List[str],
        strategy_results: Dict
    ) -> Dict:
        """Process TOC.yml to add/verify entries for created and updated files
        
        Args:
            working_directory: Path to the working directory
            created_files: List of newly created file paths
            updated_files: List of updated file paths
            strategy_results: Results from the strategy phase
            
        Returns:
            Dict with TOC update results
        """
        return self._process(working_directory, created_files, updated_files, strategy_results)
    
    def _process(
        self,
        working_directory: Path,
        created_files: List[str],
        updated_files: List[str],
        strategy_results: Dict
    ) -> Dict:
        """Internal processing logic"""
        toc_path = working_directory / "TOC.yml"
        
        # Check if TOC.yml exists
        if not toc_path.exists():
            logger.warning(f"TOC.yml not found at {toc_path}")
            return {
                'success': False,
                'message': 'TOC.yml not found in working directory',
                'toc_path': str(toc_path)
            }
        
        # Read existing TOC
        try:
            toc_content = read(toc_path, limit=None)  # Read entire file without truncation
            
            # Log TOC file info for debugging
            lines = toc_content.split('\n')
            logger.info(f"TOC.yml has {len(lines)} lines, {len(toc_content)} characters")
            if len(lines) > 10:
                logger.debug(f"First 10 lines of TOC.yml:\n{chr(10).join(lines[:10])}")
            
            existing_toc = yaml.safe_load(toc_content) or []
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse TOC.yml - YAML syntax error: {e}")
            
            # Try to extract the problematic line
            error_details = str(e)
            line_info = ""
            if "line" in error_details:
                try:
                    # Extract line number from error message
                    import re
                    line_match = re.search(r'line (\d+)', error_details)
                    if line_match:
                        line_num = int(line_match.group(1))
                        lines = toc_content.split('\n')
                        if 0 < line_num <= len(lines):
                            context_start = max(0, line_num - 3)
                            context_end = min(len(lines), line_num + 2)
                            line_info = "\nContext around error:\n"
                            for i in range(context_start, context_end):
                                prefix = ">>> " if i == line_num - 1 else "    "
                                line_info += f"{prefix}{i+1}: {lines[i]}\n"
                except Exception:
                    pass
            
            return {
                'success': False,
                'message': f'TOC.yml has invalid YAML syntax: {str(e)}',
                'toc_path': str(toc_path),
                'error_details': error_details + line_info,
                'suggestion': 'The TOC.yml file needs to be fixed manually before it can be updated automatically.'
            }
        except Exception as e:
            logger.error(f"Failed to read or parse TOC.yml: {e}")
            return {
                'success': False,
                'message': f'Failed to parse TOC.yml: {str(e)}',
                'toc_path': str(toc_path)
            }
        
        # Validate TOC structure
        if not isinstance(existing_toc, list):
            logger.error(f"TOC root is not a list, got {type(existing_toc)}")
            return {
                'success': False,
                'message': 'TOC.yml root should be a list of entries',
                'toc_path': str(toc_path)
            }
        
        # Extract all file paths from TOC
        existing_entries = self._extract_file_paths(existing_toc)
        logger.info(f"Found {len(existing_entries)} existing entries in TOC")
        
        # Find missing entries
        missing_created = [f for f in created_files if f not in existing_entries]
        missing_updated = [f for f in updated_files if f not in existing_entries]
        
        if not missing_created and not missing_updated:
            logger.info("All files already have TOC entries")
            return {
                'success': True,
                'message': 'All files already have TOC entries',
                'changes_made': False,
                'toc_path': str(toc_path)
            }
        
        # Prepare context for LLM
        toc_update_context = self._prepare_toc_context(
            toc_content,
            existing_toc,
            missing_created,
            missing_updated,
            strategy_results
        )
        
        # Call LLM to generate TOC updates
        updated_toc = self._generate_toc_updates(toc_update_context)
        
        if not updated_toc:
            return {
                'success': False,
                'message': 'Failed to generate TOC updates',
                'toc_path': str(toc_path)
            }
        
        # Save updated TOC
        preview_path = self._save_toc_preview(updated_toc['content'], working_directory)
        
        return {
            'success': True,
            'message': 'TOC updated successfully',
            'changes_made': True,
            'toc_path': str(toc_path),
            'preview_path': str(preview_path),
            'entries_added': updated_toc.get('entries_added', []),
            'entries_verified': updated_toc.get('entries_verified', []),
            'thinking': updated_toc.get('thinking', '')
        }
    
    def _extract_file_paths(self, toc_items: List[Dict], prefix: str = "") -> List[str]:
        """Recursively extract all file paths from TOC structure"""
        file_paths = []
        
        for item in toc_items:
            if isinstance(item, dict):
                # Check for href
                if 'href' in item:
                    file_paths.append(item['href'])
                
                # Check for items (nested structure)
                if 'items' in item and isinstance(item['items'], list):
                    nested_paths = self._extract_file_paths(item['items'], prefix)
                    file_paths.extend(nested_paths)
        
        return file_paths
    
    def _prepare_toc_context(
        self,
        toc_content: str,
        existing_toc: List[Dict],
        missing_created: List[str],
        missing_updated: List[str],
        strategy_results: Dict
    ) -> Dict:
        """Prepare context for TOC update"""
        # Extract strategy decisions for context
        decisions = strategy_results.get('decisions', [])
        file_descriptions = {}
        
        for decision in decisions:
            filename = decision.get('filename', '')
            if filename:
                file_descriptions[filename] = {
                    'action': decision.get('action'),
                    'content_type': decision.get('content_type', decision.get('current_content_type')),
                    'reason': decision.get('reason', ''),
                    'content_brief': decision.get('content_brief', {})
                }
                
                # Add path-based hints for placement
                if '/' in filename:
                    directory = filename.split('/')[0]
                    file_descriptions[filename]['directory_hint'] = f"File is in '{directory}' directory"
        
        # For very large TOC files, we should provide a truncated version to the LLM
        # while still maintaining the full structure for reference
        toc_for_prompt = toc_content
        if len(toc_content) > 20000:  # If TOC is larger than 20KB
            logger.info(f"TOC is large ({len(toc_content)} chars), creating condensed version for prompt")
            # Create a condensed version showing structure
            lines = toc_content.split('\n')
            condensed_lines = []
            
            # Keep first 100 lines to show structure
            condensed_lines.extend(lines[:100])
            condensed_lines.append("\n# ... [TOC continues with more entries] ...\n")
            
            # Add last 50 lines to show end structure
            condensed_lines.extend(lines[-50:])
            
            toc_for_prompt = '\n'.join(condensed_lines)
            logger.info(f"Condensed TOC for prompt: {len(toc_for_prompt)} chars")
        
        return {
            'toc_content': toc_for_prompt,  # Use condensed version for prompt
            'existing_structure': existing_toc,  # Keep full structure
            'missing_created_files': missing_created,
            'missing_updated_files': missing_updated,
            'file_descriptions': file_descriptions,
            'total_entries': len(self._extract_file_paths(existing_toc))
        }
    
    def _generate_toc_updates(self, context: Dict) -> Optional[Dict]:
        """Generate TOC updates using LLM"""
        from ..prompts.toc import get_toc_update_prompt, TOC_UPDATE_SYSTEM
        
        prompt = get_toc_update_prompt(
            context['toc_content'],
            context['missing_created_files'],
            context['missing_updated_files'],
            context['file_descriptions']
        )
        
        messages = [
            {"role": "system", "content": TOC_UPDATE_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Note: gpt-4o supports JSON response format, but gpt-4 does not
            # Models that support JSON response format: gpt-4o, gpt-4-turbo-preview, gpt-3.5-turbo (1106 and later)
            response = self._call_llm(
                messages,
                model=self.config.completion_model,
                response_format="json_object",
                operation_name="TOC Analysis"
            )
            
            # Save interaction
            self.save_interaction(
                prompt,
                response,
                "toc_update",
                "./llm_outputs/toc_management"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate TOC updates: {e}")
            
            # If JSON response format failed, try without it as a fallback
            if "response_format" in str(e):
                logger.info("Retrying without JSON response format...")
                try:
                    response = self._call_llm(
                        messages,
                        model=self.config.completion_model,
                        operation_name="TOC Analysis (Fallback)"
                        # No response_format parameter
                    )
                    
                    # Try to parse the response as JSON manually
                    import json
                    if isinstance(response, dict) and 'content' in response:
                        content = response['content']
                        # Try to extract JSON from the content
                        if content.strip().startswith('{'):
                            response = json.loads(content)
                        else:
                            # Look for JSON in code blocks
                            import re
                            json_match = re.search(r'```json?\s*(\{.*?\})\s*```', content, re.DOTALL)
                            if json_match:
                                response = json.loads(json_match.group(1))
                            else:
                                logger.error("Could not extract JSON from response")
                                return None
                    
                    # Save interaction
                    self.save_interaction(
                        prompt,
                        response,
                        "toc_update",
                        "./llm_outputs/toc_management"
                    )
                    
                    return response
                    
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    
            return None
    
    def _save_toc_preview(self, updated_toc: str, working_directory: Path) -> Path:
        """Save TOC preview"""
        preview_dir = Path("./llm_outputs/preview/toc")
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        # Use working directory name in preview filename
        working_dir_name = working_directory.name
        preview_path = preview_dir / f"TOC_{working_dir_name}.yml"
        
        write(preview_path, updated_toc)
        return preview_path 