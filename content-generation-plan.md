# Content Generation Implementation Plan

## Overview

This plan outlines the implementation of Phase 3: Content Generation for the AI Content Developer. This phase will execute the CREATE and UPDATE actions identified in Phase 2 by generating actual content using specialized prompts.

## Goals

1. Generate high-quality technical documentation for CREATE actions
2. Generate precise content updates for UPDATE actions
3. **Utilize FULL content from user materials (not just summaries)**
4. Respect content type specifications (Overview, How-To, Tutorial, etc.)
5. Maintain Microsoft documentation standards

## Architecture Design

### New Components in `prompts.py`

Following the existing pattern of prompt functions and system constants:

#### 1. CREATE Content Generation Prompts
```python
# === CONTENT GENERATION PROMPTS (CREATE) ===

def get_create_content_prompt(
    action: Dict,
    materials_full_content: Dict[str, str],
    materials_summaries: List[Dict],
    relevant_chunks: List[Dict],
    content_standards: Dict
) -> str:
    """Get the prompt for generating new content based on CREATE action"""
    # Implementation details...

CREATE_CONTENT_SYSTEM = """You are an expert technical documentation writer..."""
```

#### 2. UPDATE Content Generation Prompts
```python
# === CONTENT GENERATION PROMPTS (UPDATE) ===

def get_update_content_prompt(
    action: Dict,
    existing_content: str,
    materials_full_content: Dict[str, str],
    materials_summaries: List[Dict],
    relevant_chunks: List[Dict]
) -> str:
    """Get the prompt for updating existing content based on UPDATE action"""
    # Implementation details...

UPDATE_CONTENT_SYSTEM = """You are an expert technical documentation editor..."""
```

### New Components in `main.py`

Following the existing SmartProcessor pattern:

#### 1. ContentGenerator (Main Phase 3 Processor)
```python
class ContentGenerator(SmartProcessor):
    """Main processor for Phase 3 content generation"""
    
    def _process(self, strategy: ContentStrategy, materials: List[Dict], 
                 working_dir_path: Path, repo_name: str, 
                 working_directory: str) -> Dict:
        """
        Process all content generation actions from strategy
        Returns: Dict with generated content for all actions
        """
        # Load full material content using existing ContentExtractor
        material_loader = MaterialContentLoader(self.config)
        materials_full_content = material_loader.load_all_materials(
            self.config.support_materials,
            working_dir_path.parent.parent  # repo_path
        )
        
        # Process CREATE and UPDATE actions
        results = {
            'create_results': [],
            'update_results': [],
            'preview_dir': Path('./llm_outputs/preview')
        }
        
        # Similar to how ContentDiscoveryProcessor processes files
        create_processor = CreateContentProcessor(self.client, self.config)
        update_processor = UpdateContentProcessor(self.client, self.config)
        
        # Process actions by priority
        for action in self._sort_by_priority(strategy.decisions):
            if action.get('action') == 'CREATE':
                result = create_processor.process(
                    action, materials_full_content, 
                    materials, self._load_relevant_chunks(action)
                )
                results['create_results'].append(result)
            elif action.get('action') == 'UPDATE':
                result = update_processor.process(
                    action, materials_full_content,
                    materials, self._load_relevant_chunks(action),
                    working_dir_path
                )
                results['update_results'].append(result)
        
        return results
```

#### 2. MaterialContentLoader
```python
class MaterialContentLoader:
    """Loads full content of materials using existing ContentExtractor"""
    
    def __init__(self, config: Config):
        self.config = config
        self.extractor = ContentExtractor(config)
    
    def load_all_materials(self, materials: List[str], 
                          repo_path: Path) -> Dict[str, str]:
        """Load full content of all materials"""
        materials_content = {}
        
        for material in materials:
            content = self.extractor.extract(material, repo_path)
            if content:
                materials_content[material] = content
                # Cache for reuse
                cache_path = Path(f"./llm_outputs/materials_cache/{get_hash(material)}.txt")
                fileops.mkdir(cache_path.parent)
                fileops.write(cache_path, content)
            else:
                logger.warning(f"Could not extract content from {material}")
        
        return materials_content
```

#### 3. CreateContentProcessor
```python
class CreateContentProcessor(SmartProcessor):
    """Processor for generating new content files"""
    
    def _process(self, action: Dict, materials_full_content: Dict[str, str],
                 materials_summaries: List[Dict], 
                 relevant_chunks: List[DocumentChunk]) -> Dict:
        """Generate new content based on CREATE action"""
        
        # Load content standards
        standards = self._load_content_standards()
        
        # Get content type template
        content_type = action.get('content_type', 'How-To Guide')
        
        # Prepare chunks for prompt
        chunk_data = self._prepare_chunk_data(relevant_chunks)
        
        # Generate content
        prompt = get_create_content_prompt(
            action, materials_full_content, materials_summaries,
            chunk_data, standards
        )
        system = CREATE_CONTENT_SYSTEM
        
        try:
            result = self.llm_call(system, prompt, "gpt-4o")
            
            # Save interaction
            self.save_interaction(
                prompt, result, "create_content",
                "./llm_outputs/content_generation/create",
                action.get('filename', 'unknown.md')
            )
            
            # Extract generated content
            content = result.get('content', '')
            
            # Save to preview
            preview_path = Path(f"./llm_outputs/preview/create/{action['filename']}")
            fileops.mkdir(preview_path.parent)
            fileops.write(preview_path, content)
            
            return {
                'action': action,
                'content': content,
                'preview_path': str(preview_path),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to generate content for {action['filename']}: {e}")
            return {
                'action': action,
                'error': str(e),
                'success': False
            }
    
    def _load_content_standards(self) -> Dict:
        """Reuse from ContentStrategyProcessor"""
        standards_path = Path("content_standards.json")
        if standards_path.exists():
            return fileops.load_json(standards_path)
        else:
            return {...}  # Default standards
```

#### 4. UpdateContentProcessor
```python
class UpdateContentProcessor(SmartProcessor):
    """Processor for updating existing content files"""
    
    def _process(self, action: Dict, materials_full_content: Dict[str, str],
                 materials_summaries: List[Dict],
                 relevant_chunks: List[DocumentChunk],
                 working_dir_path: Path) -> Dict:
        """Update existing content based on UPDATE action"""
        
        # Read existing file
        file_path = working_dir_path / action['filename']
        if not file_path.exists():
            logger.error(f"File not found: {action['filename']}")
            return {'action': action, 'error': 'File not found', 'success': False}
        
        existing_content = fileops.read(file_path, limit=None)
        
        # Prepare chunks for prompt
        chunk_data = self._prepare_chunk_data(relevant_chunks)
        
        # Generate updated content
        prompt = get_update_content_prompt(
            action, existing_content, materials_full_content,
            materials_summaries, chunk_data
        )
        system = UPDATE_CONTENT_SYSTEM
        
        try:
            result = self.llm_call(system, prompt, "gpt-4o")
            
            # Save interaction
            self.save_interaction(
                prompt, result, "update_content",
                "./llm_outputs/content_generation/update",
                action.get('filename', 'unknown.md')
            )
            
            # Extract updated content
            updated_content = result.get('updated_content', existing_content)
            
            # Save to preview
            preview_path = Path(f"./llm_outputs/preview/update/{action['filename']}")
            fileops.mkdir(preview_path.parent)
            fileops.write(preview_path, updated_content)
            
            # Generate diff for review
            diff = self._generate_diff(existing_content, updated_content)
            diff_path = preview_path.with_suffix('.diff')
            fileops.write(diff_path, diff)
            
            return {
                'action': action,
                'updated_content': updated_content,
                'preview_path': str(preview_path),
                'diff_path': str(diff_path),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to update content for {action['filename']}: {e}")
            return {
                'action': action,
                'error': str(e),
                'success': False
            }
```

### Integration with Existing Orchestrator

Update ContentDeveloperOrchestrator in `main.py`:

```python
class ContentDeveloperOrchestrator:
    def execute(self) -> Result:
        logger.info(f"=== Content Developer: Phase(s) {self.config.phases} ===")
        
        # ... existing Phase 1 and 2 code ...
        
        # Phase 3
        if '3' in self.config.phases:
            if not result.strategy_ready:
                logger.error("Phase 3 requires completed Phase 2 strategy")
                return result
            
            try:
                logger.info("=== Phase 3: Content Generation ===")
                
                # Use ContentGenerator following same pattern as Phase 2
                generator = ContentGenerator(self.client, self.config)
                generation_results = generator.process(
                    result.content_strategy,
                    result.material_summaries,
                    working_dir_path,
                    self.repo_manager.extract_name(self.config.repo_url),
                    confirmed['working_directory']
                )
                
                # Store results in Result dataclass (extend it)
                result.generation_results = generation_results
                result.generation_ready = True
                
                # Apply to repository if requested
                if self.config.apply_changes:
                    self._apply_generated_content(generation_results, working_dir_path)
                
                logger.info(f"Phase 3 completed: Generated {len(generation_results['create_results'])} new files, "
                          f"updated {len(generation_results['update_results'])} files")
                
            except Exception as e:
                logger.error(f"Phase 3 failed: {e}")
                result.generation_results = None
                result.generation_ready = False
        
        return result
```

### Update Result Dataclass

```python
@dataclass
class Result:
    # ... existing fields ...
    content_strategy: Optional[ContentStrategy] = None
    strategy_ready: bool = False
    # New fields for Phase 3
    generation_results: Optional[Dict] = None
    generation_ready: bool = False
```

### Update Config Dataclass

```python
@dataclass
class Config:
    # ... existing fields ...
    phases: str = "1"  # Already supports "123", "23", "3"
    apply_changes: bool = False  # New field for --apply flag
```

### Update Command Line Arguments

In `main()` function:

```python
def main():
    parser = argparse.ArgumentParser(
        # ... existing description ...
        epilog="""
Hyper-Compact Modular Design - Maximum reusability, minimal code
• Phase 1: Repository analysis & working directory selection
• Phase 2: Content strategy with CREATE/UPDATE recommendations
• Phase 3: Content generation for CREATE/UPDATE actions
• Intelligent LLM → Interactive fallback • Auto-confirm for CI/CD

Examples:
  python main.py https://github.com/Azure/azure-docs --goal "Document feature" --service compute
  python main.py https://github.com/Azure/azure-docs --goal "Storage guide" --service storage --materials doc.md --phases 123
  python main.py https://github.com/Azure/azure-docs --goal "Document Cilium" --service aks --phases 3 --apply"""
    )
    
    # ... existing arguments ...
    parser.add_argument('--apply', action='store_true', 
                       help='Apply generated content to repository (default: preview only)')
```

### Output Directory Structure

All outputs follow existing patterns:

```
./llm_outputs/
├── materials_summary/        # Phase 1 (existing)
├── decisions/               # Phase 1 (existing)
├── content_strategy/        # Phase 2 (existing)
├── embeddings/             # Phase 2 (existing)
├── content_generation/     # Phase 3 (new)
│   ├── create/
│   │   ├── [timestamp]_[filename]_prompt.txt
│   │   └── [timestamp]_[filename]_response.json
│   └── update/
│       ├── [timestamp]_[filename]_prompt.txt
│       └── [timestamp]_[filename]_response.json
├── materials_cache/        # Phase 3 (new)
│   └── [material_hash].txt
└── preview/               # Phase 3 (new)
    ├── create/
    │   └── [filename].md
    └── update/
        ├── [filename].md
        └── [filename].diff
```

## Implementation Notes

1. **Reuse Existing Components**:
   - Use `ContentExtractor` for loading materials
   - Follow `SmartProcessor` pattern for all processors
   - Use existing `save_interaction` method
   - Reuse `_load_content_standards` logic

2. **Maintain Consistency**:
   - All processors inherit from `SmartProcessor`
   - Follow existing error handling patterns
   - Use existing logging approach
   - Maintain existing file operations through `fileops`

3. **Data Flow**:
   - Phase 1: Produces `material_summaries`
   - Phase 2: Produces `content_strategy` with `decisions`
   - Phase 3: Uses both to generate content
   - Results accumulate in `Result` dataclass

4. **No Changes to Existing Phases**:
   - Phase 1 and 2 remain untouched
   - Only add new processors and extend orchestrator
   - Existing prompts in `prompts.py` unchanged

## Conclusion

This implementation seamlessly integrates Phase 3 into the existing architecture by following established patterns and reusing existing components. The design maintains consistency with Phases 1 and 2 while adding powerful content generation capabilities. 