"""
Main orchestrator for AI Content Developer
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from ..interactive.directory import DirectoryConfirmation
from ..interactive.strategy import StrategyConfirmation
from ..models import Config, Result
from ..processors import (
    ContentDiscoveryProcessor, ContentStrategyProcessor, DirectoryDetector,
    MaterialProcessor, TOCProcessor
)
from ..generation import ContentGenerator
from ..repository import RepositoryManager
from ..utils import write, mkdir, setup_logging
from ..constants import MAX_PHASES

logger = logging.getLogger(__name__)


class ContentDeveloperOrchestrator:
    """Main orchestrator for content development workflow"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize Azure OpenAI client with Entra ID authentication
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        
        self.client = AzureOpenAI(
            azure_endpoint=config.azure_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=config.api_version,
        )
        
        self.repo_manager = RepositoryManager()
        self.dir_confirmator = DirectoryConfirmation(config)
        self.strategy_confirmator = StrategyConfirmation(config)
        setup_logging()
    
    def execute(self) -> Result:
        """Execute the content development workflow"""
        # Parse phases configuration
        max_phase = self._parse_max_phase()
        phase_display = self.config.phases if self.config.phases != "all" else f"1-{max_phase}"
        logger.info(f"=== Content Developer: Phase(s) {phase_display} ===")
        
        # Execute Phase 1 (always runs)
        result = self._execute_phase1()
        
        # Execute Phase 2 if requested
        if max_phase >= 2 and result.directory_ready:
            self._execute_phase2(result)
        
        # Execute Phase 3 if requested
        if max_phase >= 3 and result.strategy_ready:
            self._execute_phase3(result)
        
        # Execute Phase 4 if requested
        if max_phase >= 4 and result.generation_ready and not self.config.skip_toc:
            self._execute_phase4(result)
        elif max_phase >= 4 and self.config.skip_toc:
            logger.info("=== Phase 4: TOC Management (SKIPPED) ===")
            logger.info("TOC management skipped due to --skip-toc flag")
        
        return result
    
    def _parse_max_phase(self) -> int:
        """Parse the maximum phase to execute from config"""
        if self.config.phases == "all":
            max_phase = MAX_PHASES
        elif self.config.phases.isdigit():
            max_phase = int(self.config.phases)
        else:
            # Handle combinations like "123", "34", etc.
            max_phase = max(int(p) for p in self.config.phases if p.isdigit()) if any(p.isdigit() for p in self.config.phases) else 1
        
        logger.info(f"Phases parsing: config.phases='{self.config.phases}' -> max_phase={max_phase}")
        return max_phase
    
    def _execute_phase1(self) -> Result:
        """Execute Phase 1: Repository Analysis & Directory Selection"""
        logger.info("=== Phase 1: Repository Analysis ===")
        
        # Clone/update repository
        repo_path = self.repo_manager.clone_or_update(self.config.repo_url, self.config.work_dir)
        
        # Process materials
        materials = MaterialProcessor(self.client, self.config).process(
            self.config.support_materials, repo_path
        )
        
        # Get repository structure
        structure = self.repo_manager.get_structure(repo_path, self.config.max_repo_depth)
        
        # Detect working directory with LLM
        llm_result, llm_failed, error = self._detect_directory(repo_path, structure, materials)
        
        # In auto-confirm mode, check if the selection is valid
        if self.config.auto_confirm:
            if llm_failed:
                logger.error(f"Directory selection failed in auto-confirm mode: {error}")
                raise RuntimeError(f"Auto-confirm enabled but LLM failed: {error}")
            
            # Check if the result indicates a failure (empty directory, low confidence, or error)
            if not llm_result.get('working_directory'):
                error_msg = llm_result.get('error', 'LLM returned empty directory')
                logger.error(f"Directory selection failed in auto-confirm mode: {error_msg}")
                raise RuntimeError(f"Auto-confirm enabled but directory selection failed: {error_msg}")
            
            if llm_result.get('confidence', 0) < 0.7:
                logger.error(f"Directory selection confidence too low in auto-confirm mode: {llm_result.get('confidence', 0):.2f}")
                logger.error(f"Selected directory: {llm_result.get('working_directory')}")
                raise RuntimeError(f"Auto-confirm enabled but confidence too low: {llm_result.get('confidence', 0):.2f}")
        
        # Confirm directory selection (in auto-confirm mode, this will just pass through)
        confirmed = self.dir_confirmator.confirm(llm_result, structure, llm_failed, error)
        
        # Setup directory
        setup_result = self._setup_directory(repo_path, confirmed['working_directory'])
        
        # Create and return result
        return self._create_phase1_result(confirmed, setup_result, repo_path, materials)
    
    def _detect_directory(self, repo_path: Path, structure: str, 
                         materials: list) -> Tuple[Optional[Dict], bool, str]:
        """Detect working directory using LLM"""
        try:
            llm_result = DirectoryDetector(self.client, self.config).process(
                repo_path, structure, materials
            )
            return llm_result, False, ""
        except Exception as e:
            logger.warning(f"LLM failed: {e}")
            return None, True, str(e)
    
    def _create_phase1_result(self, confirmed: Dict, setup_result: Dict, 
                             repo_path: Path, materials: list) -> Result:
        """Create Result object from Phase 1 outputs"""
        return Result(
            working_directory=confirmed['working_directory'],
            justification=confirmed['justification'],
            confidence=confirmed['confidence'],
            repo_url=self.config.repo_url,
            repo_path=str(repo_path),
            material_summaries=materials,
            content_goal=self.config.content_goal,
            service_area=self.config.service_area,
            directory_ready=setup_result['success'],
            working_directory_full_path=setup_result.get('full_path'),
            setup_error=setup_result.get('error')
        )
    
    def _execute_phase2(self, result: Result) -> None:
        """Execute Phase 2: Content Strategy Analysis"""
        logger.info("=== Phase 2: Content Strategy Analysis ===")
        
        try:
            # Get working directory path
            working_dir_path = Path(result.working_directory_full_path)
            
            # Discover content chunks
            chunks = self._discover_content(working_dir_path, result.working_directory)
            
            # Generate content strategy
            strategy = self._generate_strategy(chunks, result.material_summaries, 
                                             result.working_directory)
            
            # Confirm strategy
            confirmed_strategy = self.strategy_confirmator.confirm(strategy)
            
            # Update result
            result.content_strategy = confirmed_strategy
            result.strategy_ready = confirmed_strategy.confidence > 0
            
            logger.info(f"Phase 2 completed: {confirmed_strategy.summary}")
            
        except Exception as e:
            self._handle_phase2_error(result, e)
    
    def _discover_content(self, working_dir_path: Path, working_directory: str) -> list:
        """Discover and chunk content in the working directory"""
        chunks = ContentDiscoveryProcessor(self.client, self.config).process(
            working_dir_path,
            self.repo_manager.extract_name(self.config.repo_url),
            working_directory
        )
        logger.info(f"ContentDiscoveryProcessor returned {len(chunks)} chunks")
        return chunks
    
    def _generate_strategy(self, chunks: list, materials: list, 
                          working_directory: str) -> 'ContentStrategy':
        """Generate content strategy based on discovered chunks"""
        strategy = ContentStrategyProcessor(self.client, self.config).process(
            chunks, materials, self.config,
            self.repo_manager.extract_name(self.config.repo_url),
            working_directory
        )
        logger.info(f"ContentStrategyProcessor returned strategy: {strategy.summary[:50]}...")
        return strategy
    
    def _handle_phase2_error(self, result: Result, error: Exception) -> None:
        """Handle Phase 2 execution errors"""
        import traceback
        logger.error(f"Phase 2 failed with exception: {type(error).__name__}: {error}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        error_strategy = self.strategy_confirmator.confirm(None, True, str(error))
        result.content_strategy = error_strategy
        result.strategy_ready = False
    
    def _execute_phase3(self, result: Result) -> None:
        """Execute Phase 3: Content Generation"""
        logger.info("=== Phase 3: Content Generation ===")
        
        try:
            # Get working directory path
            working_dir_path = Path(result.working_directory_full_path)
            
            # Generate content
            generation_results = self._generate_content(
                result, working_dir_path, result.working_directory
            )
            
            # Store results
            result.generation_results = generation_results
            result.generation_ready = True
            
            # Apply changes if requested
            if self.config.apply_changes:
                self._apply_generated_content(generation_results, working_dir_path)
                # Set applied flag to indicate changes were written to repository
                generation_results['applied'] = True
            else:
                # Set applied flag to false to indicate preview mode
                generation_results['applied'] = False
            
            # Log summary
            self._log_generation_summary(generation_results)
            
        except Exception as e:
            self._handle_phase3_error(result, e)
    
    def _generate_content(self, result: Result, working_dir_path: Path, 
                         working_directory: str) -> Dict:
        """Generate content using ContentGenerator"""
        generator = ContentGenerator(self.client, self.config)
        return generator.process(
            result.content_strategy,
            result.material_summaries,
            working_dir_path,
            self.repo_manager.extract_name(self.config.repo_url),
            working_directory
        )
    
    def _log_generation_summary(self, generation_results: Dict) -> None:
        """Log content generation summary"""
        create_count = sum(1 for result in generation_results.get('create_results', []) 
                          if result.get('success'))
        update_count = sum(1 for result in generation_results.get('update_results', []) 
                          if result.get('success'))
        
        logger.info(f"Phase 3 completed: Generated {create_count} new files, "
                   f"updated {update_count} files")
    
    def _handle_phase3_error(self, result: Result, error: Exception) -> None:
        """Handle Phase 3 execution errors"""
        logger.error(f"Phase 3 failed: {error}")
        result.generation_results = None
        result.generation_ready = False
    
    def _apply_generated_content(self, generation_results: Dict, working_dir_path: Path):
        """Apply generated content to the repository"""
        logger.info("Applying generated content to repository...")
        
        # Apply CREATE actions
        self._apply_create_actions(generation_results.get('create_results', []), 
                                  working_dir_path)
        
        # Apply UPDATE actions
        self._apply_update_actions(generation_results.get('update_results', []), 
                                  working_dir_path)
    
    def _apply_create_actions(self, create_results: list, working_dir_path: Path) -> None:
        """Apply CREATE actions to create new files"""
        for result in create_results:
            if result.get('success') and result.get('content'):
                self._create_file(result, working_dir_path)
    
    def _create_file(self, result: Dict, working_dir_path: Path) -> None:
        """Create a new file from generation result"""
        filename = result['action'].get('filename', '')
        file_path = working_dir_path / filename
        
        # Ensure directory exists
        mkdir(file_path.parent)
        
        # Write content
        write(file_path, result['content'])
        logger.info(f"Created: {filename}")
    
    def _apply_update_actions(self, update_results: list, working_dir_path: Path) -> None:
        """Apply UPDATE actions to modify existing files"""
        for result in update_results:
            if result.get('success') and result.get('updated_content'):
                self._update_file(result, working_dir_path)
    
    def _update_file(self, result: Dict, working_dir_path: Path) -> None:
        """Update an existing file from generation result"""
        filename = result['action'].get('filename', '')
        file_path = working_dir_path / filename
        
        # Write updated content
        write(file_path, result['updated_content'])
        logger.info(f"Updated: {filename}")
    
    def _setup_directory(self, repo_path: Path, working_dir: str) -> Dict:
        """Setup and validate working directory"""
        # Strip repository name if included
        working_dir = self._normalize_working_directory(repo_path, working_dir)
        
        # Get full path
        full_path = repo_path / working_dir
        
        # Validate directory
        validation_result = self._validate_directory(full_path, working_dir)
        if validation_result:
            return validation_result
        
        # Check for markdown files
        md_count = self._count_markdown_files(full_path)
        
        return {
            'success': True,
            'full_path': str(full_path),
            'markdown_count': md_count
        }
    
    def _normalize_working_directory(self, repo_path: Path, working_dir: str) -> str:
        """Normalize working directory path by removing repo name if present"""
        repo_name = repo_path.name
        if working_dir.startswith(f"{repo_name}/"):
            working_dir = working_dir[len(repo_name)+1:]
            logger.info(f"Stripped repo name from working_dir: {repo_name}/ -> {working_dir}")
        return working_dir
    
    def _validate_directory(self, full_path: Path, working_dir: str) -> Optional[Dict]:
        """Validate that the directory exists and is a directory"""
        if not full_path.exists():
            return {
                'success': False,
                'error': f"Directory does not exist: {working_dir}",
                'full_path': str(full_path)
            }
        
        if not full_path.is_dir():
            return {
                'success': False,
                'error': f"Not a directory: {working_dir}",
                'full_path': str(full_path)
            }
        
        return None
    
    def _count_markdown_files(self, directory: Path) -> int:
        """Count markdown files in directory"""
        md_files = list(directory.rglob("*.md"))
        if not md_files:
            logger.warning(f"No markdown files found in {directory}")
            logger.info("This may indicate a non-content directory was selected (e.g., media/assets directory)")
            logger.info("Consider re-running with a different content goal or checking the selected directory")
        return len(md_files)
    
    def _execute_phase4(self, result: Result) -> None:
        """Execute Phase 4: TOC Management"""
        logger.info("=== Phase 4: TOC Management ===")
        
        try:
            # Get working directory path
            working_dir_path = Path(result.working_directory_full_path)
            
            # Run TOC management
            toc_results = self._run_toc_phase(
                working_dir_path,
                result.generation_results.get('created_files', []),
                result.generation_results.get('updated_files', []),
                result.content_strategy
            )
            
            # Update result
            result.toc_results = toc_results
            result.toc_ready = True
            
            # Apply TOC changes if requested and successful
            if self.config.apply_changes and toc_results.get('success') and toc_results.get('changes_made'):
                self._apply_toc_changes(toc_results, working_dir_path)
                toc_results['applied'] = True
            else:
                toc_results['applied'] = False
            
            logger.info(f"Phase 4 completed: {toc_results.get('message', 'No message')}")
            
        except Exception as e:
            self._handle_phase4_error(result, e)
    
    def _run_toc_phase(self, working_dir_path: Path, created_files: list, updated_files: list, 
                      strategy: 'ContentStrategy') -> Dict:
        """Run TOC management phase"""
        toc_processor = TOCProcessor(self.client, self.config)
        return toc_processor.process(
            working_dir_path,
            created_files,
            updated_files,
            {
                'decisions': strategy.decisions if hasattr(strategy, 'decisions') else []
            }
        )
    
    def _apply_toc_changes(self, toc_results: Dict, working_dir_path: Path) -> None:
        """Apply TOC changes to the repository"""
        logger.info("Applying TOC changes to repository...")
        
        toc_path = working_dir_path / "TOC.yml"
        
        # The LLM should have returned the complete updated TOC content
        updated_content = toc_results.get('content', '')
        
        if not updated_content:
            logger.error("No TOC content to apply")
            return
        
        # Write the updated TOC
        write(toc_path, updated_content)
        logger.info(f"Updated: TOC.yml")
        
        # Log which entries were added
        entries_added = toc_results.get('entries_added', [])
        if entries_added:
            logger.info(f"Added {len(entries_added)} entries to TOC: {', '.join(entries_added)}")
    
    def _handle_phase4_error(self, result: Result, error: Exception) -> None:
        """Handle Phase 4 execution errors"""
        logger.error(f"Phase 4 failed: {error}")
        result.toc_results = None
        result.toc_ready = False 