# AI Content Developer (ACD) - Project Restructuring Plan

## Overview

This document outlines the plan to restructure the current hyper-compact AI Content Developer from a single `main.py` file into a properly organized project following Python best practices. The new structure will support existing Phase 1 & 2 functionality while providing a foundation for future phases aligned with the Doc Buddy Workflow Orchestrator design.

## Current State

- **Single File**: 1,256 lines in `main.py` containing all functionality
- **Separate Files**: `prompts.py` (253 lines) and `requirements.txt`
- **Phases Implemented**:
  - Phase 1: Repository Analysis & Working Directory Selection
  - Phase 2: Content Strategy Generation (CREATE/UPDATE actions)

## Proposed Project Structure

```
app/
├── __init__.py
├── __main__.py              # Entry point for python -m app
├── cli.py                   # Command-line interface
├── config.py                # Configuration management
├── models/                  # Data models
│   ├── __init__.py
│   ├── base.py             # Base dataclasses
│   ├── content.py          # Content-related models
│   └── strategy.py         # Strategy-related models
├── core/                    # Core business logic
│   ├── __init__.py
│   ├── cache.py            # Unified caching system
│   ├── embeddings.py       # Embedding management
│   ├── extraction.py       # Content extraction
│   └── repository.py       # Git repository management
├── processors/              # LLM processors
│   ├── __init__.py
│   ├── base.py             # Base processor class
│   ├── material.py         # Material analysis
│   ├── directory.py        # Directory detection
│   ├── discovery.py        # Content discovery
│   ├── strategy.py         # Strategy generation
│   ├── content.py          # Content generation
│   └── review.py           # Review pipeline processors
├── phases/                  # Phase implementations
│   ├── __init__.py
│   ├── phase1.py           # Repository Setup & Understanding
│   ├── phase2.py           # Content Strategy Decision
│   ├── phase3.py           # Content Operations (Create/Update)
│   ├── phase4.py           # Review Pipeline (4-stage)
│   ├── phase5.py           # Repository Integration
│   └── phase6.py           # Completion & Validation
├── ui/                      # User interface components
│   ├── __init__.py
│   ├── interactive.py      # Interactive confirmations
│   ├── display.py          # Result display
│   └── progress.py         # Progress tracking
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── functional.py       # Functional utilities
│   ├── file_ops.py         # File operations
│   ├── logging.py          # Logging setup
│   └── imports.py          # Dynamic imports
├── prompts/                 # Prompt management
│   ├── __init__.py
│   ├── material.py         # Material processing prompts
│   ├── directory.py        # Directory selection prompts
│   ├── strategy.py         # Strategy generation prompts
│   ├── content.py          # Content generation prompts
│   ├── review.py           # Review pipeline prompts
│   └── integration.py      # Integration prompts
└── orchestrator.py          # Main orchestration logic
```

## Implementation Plan

### Phase 1: Core Restructuring (Week 1)

1. **Setup Project Structure**
   - Create all directories and `__init__.py` files
   - Move `requirements.txt` to project root
   - Create `setup.py` for package installation
   - Add `README.md` with project overview

2. **Extract Utilities**
   - Move functional utilities (`compose`, `pipe`, `safe_get`, `safe_call`, `get_hash`, `chunk_text`) to `utils/functional.py`
   - Move `FileOps` class to `utils/file_ops.py`
   - Move `setup_logging` to `utils/logging.py`
   - Move `safe_import` and `error_handler` to `utils/imports.py`

3. **Extract Data Models**
   - Move `Config` dataclass to `models/base.py`
   - Move `ContentStrategy`, `DocumentChunk`, `Result` to appropriate model files
   - Create model registry in `models/__init__.py`

4. **Extract Core Components**
   - Move `UnifiedCache` to `core/cache.py`
   - Move embedding-related functions from `ContentStrategyProcessor` to `core/embeddings.py`
   - Move `ContentExtractor` to `core/extraction.py`
   - Move `RepositoryManager` to `core/repository.py`

### Phase 2: Processor Migration (Week 1-2)

1. **Setup Base Processor**
   - Move `SmartProcessor` to `processors/base.py`
   - Extract common LLM call and interaction saving logic

2. **Migrate Individual Processors**
   - `MaterialProcessor` → `processors/material.py`
   - `DirectoryDetector` → `processors/directory.py`
   - `ContentDiscoveryProcessor` → `processors/discovery.py`
   - `ContentStrategyProcessor` → `processors/strategy.py`
   - Extract `SmartChunker` to `processors/chunker.py`

3. **Refactor Prompts**
   - Split `prompts.py` into module structure:
     - `prompts/material.py` - Material summary prompts
     - `prompts/directory.py` - Directory selection prompts
     - `prompts/strategy.py` - Content strategy prompts
   - Add prompt versioning support
   - Create prompt template system

### Phase 3: UI Components (Week 2)

1. **Extract Interactive Components**
   - Move `GenericInteractive` to `ui/interactive.py`
   - Move `DirectoryConfirmation` and `StrategyConfirmation` to appropriate submodules
   - Move `InteractiveSelector` with paginated selection and search

2. **Extract Display Components**
   - Move `display_results` to `ui/display.py`
   - Add result formatters for both Rich and plain text
   - Create export functionality for results

3. **Add Progress Tracking**
   - Create progress wrapper in `ui/progress.py` using Rich Progress
   - Add progress hooks to processors
   - Support both Rich and basic progress indicators

### Phase 4: Phase System Implementation (Week 2-3)

1. **Create Phase Framework**
   - Define IPhase interface in `phases/__init__.py`
   - Implement phase registry
   - Add phase dependency management

2. **Migrate Existing Phases**
   - Phase 1: Extract repository setup logic from orchestrator
   - Phase 2: Extract content strategy logic from orchestrator
   - Create phase configuration system

3. **Implement New Phases**
   - Phase 3: Content Operations (using strategy results)
   - Phase 4: Review Pipeline (4-stage review process)
   - Phase 5: Repository Integration
   - Phase 6: Completion & Validation

### Phase 5: Integration & Testing (Week 3)

1. **Create Orchestrator**
   - Move `ContentDeveloperOrchestrator` to `orchestrator.py`
   - Implement phase pipeline with proper error handling
   - Add recovery mechanisms for failed phases

2. **Setup CLI**
   - Move argument parsing from `main()` to `cli.py`
   - Add subcommands for different operations
   - Implement configuration file support (acd.yaml)

3. **Add Testing**
   - Create `tests/` directory structure
   - Add unit tests for each module
   - Add integration tests for phase workflows
   - Setup CI/CD pipeline with GitHub Actions

## Phase Specifications

### Phase 1: Repository Setup & Understanding
- **Current Functionality**: Repository analysis & working directory selection
- **Implementation Details**:
  - **MaterialProcessor**: 
    - Processes supporting materials (files, URLs, stdin)
    - Extracts content from DOCX, PDF, MD, and web pages
    - Uses `get_material_summary_prompt` to analyze technical documents
    - Extracts: main topic, technologies, key concepts, Microsoft products, document type
    - Saves interactions to `./llm_outputs/materials_summary/`
  - **DirectoryDetector**:
    - Uses `get_directory_selection_prompt` to analyze repository structure
    - Considers content goal, service area, and material summaries
    - Selects optimal working directory with confidence score
    - Uses GPT-4o model for better accuracy
    - Saves interactions to `./llm_outputs/decisions/working_directory/`
  - **Interactive Fallback**:
    - DirectoryConfirmation with paginated directory browser
    - Manual directory selection if LLM fails
    - Search functionality for large repositories
  - **Repository Management**:
    - Clone or update existing repositories
    - Generate directory structure (max depth 3)
    - Focus on .md, .yml, .yaml files

### Phase 2: Content Strategy Decision
- **Current Functionality**: Generate CREATE/UPDATE strategy based on semantic search with content type selection
- **Implementation Details**:
  - **ContentDiscoveryProcessor**:
    - Chunks markdown files using SmartChunker (3000 char chunks)
    - Parses YAML frontmatter and maintains heading hierarchy
    - Creates embedding content with context (title, topic, description, section)
    - Caches embeddings by file SHA-256 hash
    - Parallel processing for multiple files
    - Links chunks (prev/next/parent relationships)
  - **ContentStrategyProcessor**:
    - Creates intent embedding from goal, service area, and materials
    - Performs semantic search using cosine similarity
    - Applies contextual boosts:
      - File relevance boost (0.1x if file avg > 0.5)
      - Proximity boosts (0.05 for adjacent chunks > 0.6)
      - Parent section boost (0.03 if parent > 0.7)
    - Debug mode (`--debug-similarity`) shows:
      - Base similarity scores
      - File-level relevance analysis
      - Boost calculations
      - Score transformations
      - Strategy insights
    - Uses `get_content_strategy_prompt` to generate actions
    - Returns CREATE and UPDATE actions with filenames and reasons
  - **Content Type Enhancement**:
    - For CREATE actions:
      - Uses `get_content_type_selection_prompt` with LLM
      - Analyzes content goal, filename, and materials
      - Selects from Microsoft content types (Overview, Concept, Quickstart, How-To, Tutorial)
      - Adds content_type, ms_topic, and justification to each action
    - For UPDATE actions:
      - Extracts ms.topic from existing markdown frontmatter
      - Maps ms.topic to content type name
      - Handles both chunk-cached and direct file reading
    - Loads content standards from `content_standards.json`
  - **Strategy Confirmation**:
    - Interactive display of strategy summary
    - Shows top 3 CREATE and UPDATE actions with content types
    - Displays ms.topic values for each action
    - Manual override option

### Phase 3: Content Operations
- **Purpose**: Execute the chosen strategy to create or update content
- **Features**:
  - **Create Operations**:
    - Generate customer intent
    - Determine optimal placement
    - Use content type templates
    - Follow Microsoft style guide
  - **Update Operations**:
    - Read current content
    - Generate change descriptions
    - Preserve valuable sections
    - Update metadata

### Phase 4: Review Pipeline
- **Purpose**: Ensure quality, security, and alignment through comprehensive reviews
- **Review Stages**:
  1. **SEO Review**
     - Title optimization
     - Meta description generation
     - Keyword analysis
     - URL path suggestions
  2. **Security Review**
     - Detect hardcoded secrets
     - Find unsafe examples
     - Security warning checks
     - Safe placeholder suggestions
  3. **Technical Accuracy Review**
     - Fact verification
     - API version checks
     - Code sample validation
     - Technical correctness
  4. **Goal Alignment Review**
     - Goal fulfillment scoring
     - Customer intent alignment
     - Completeness check
     - Audience appropriateness

### Phase 5: Repository Integration
- **Purpose**: Write content to repository and update navigation/metadata
- **Features**:
  - Safe file operations
  - TOC.yml management
  - Redirection management
  - Cross-reference updates

### Phase 6: Completion & Validation
- **Purpose**: Final validation and summary generation
- **Features**:
  - Standards validation
  - Change summary generation
  - Impact analysis
  - Follow-up suggestions
  - Comprehensive reporting

## Migration Benefits

1. **Maintainability**: Clear separation of concerns
2. **Testability**: Isolated components for unit testing
3. **Extensibility**: Easy to add new phases and features
4. **Reusability**: Shared components across phases
5. **Scalability**: Modular architecture supports growth
6. **Documentation**: Clear module structure aids understanding

## Configuration Management

### Environment Variables
```env
OPENAI_API_KEY=xxx
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
ACD_LOG_LEVEL=INFO
ACD_CACHE_DIR=./acd/cache
ACD_OUTPUT_DIR=./acd/llm_outputs
```

### Configuration File (acd.yaml)
```yaml
version: "1.0"
defaults:
  model: "gpt-4o-mini"  # Default for most operations
  strategy_model: "gpt-4o"  # For directory selection and strategy
  embedding_model: "text-embedding-3-small"
  temperature: 0.3
  max_retries: 3
  
phases:
  phase1:
    enabled: true
    timeout: 300
    options:
      content_limit: 15000  # Max chars per material
      max_repo_depth: 3     # Directory tree depth
  phase2:
    enabled: true
    timeout: 600
    options:
      chunk_size: 3000
      min_chunk_size: 500
      max_similar_chunks: 40
      similarity_threshold: 0.35
      debug_similarity: false
  phase3:
    enabled: true
    timeout: 900
    options:
      content_standards_dir: "./templates"
  phase4:
    enabled: true
    timeout: 600
    options:
      review_stages: ["seo", "security", "technical", "goal"]
      approval_thresholds:
        security: 1.0  # Must pass all security checks
        technical: 0.7
        goal: 0.7
  phase5:
    enabled: true
    timeout: 300
  phase6:
    enabled: true
    timeout: 300
```

## Development Guidelines

1. **Code Style**:
   - Follow PEP 8
   - Use type hints throughout
   - Document all public APIs
   - Keep functions under 50 lines

2. **Error Handling**:
   - Use custom exceptions
   - Implement graceful degradation
   - Log all errors appropriately
   - Provide user-friendly messages

3. **Performance**:
   - Lazy loading for optional dependencies
   - Efficient caching strategies
   - Parallel processing where applicable
   - Memory-conscious implementations

4. **Security**:
   - Secure API key handling
   - Input validation
   - Safe file operations
   - Sandboxed code execution

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock external dependencies
- Achieve 80%+ code coverage
- Test error conditions

### Integration Tests
- Test phase interactions
- Test with real repositories
- Test with various file types
- Test error recovery

### Performance Tests
- Benchmark processing times
- Test with large repositories
- Monitor memory usage
- Test concurrent operations

## Documentation Requirements

1. **User Documentation**:
   - Getting started guide
   - Configuration reference
   - Phase documentation
   - Troubleshooting guide

2. **Developer Documentation**:
   - Architecture overview
   - API reference
   - Contributing guidelines
   - Plugin development guide

## Success Metrics

1. **Code Quality**:
   - Pylint score > 9.0
   - Test coverage > 80%
   - No critical security issues
   - Documentation coverage > 90%

2. **Performance**:
   - Phase 1 < 30s for typical repo
   - Phase 2 < 60s with caching
   - Memory usage < 500MB
   - Support repos with 10k+ files

3. **Usability**:
   - Clear error messages
   - Intuitive CLI interface
   - Comprehensive help system
   - Minimal configuration required

## Timeline

- **Week 1**: Core restructuring and utilities
- **Week 2**: Processors and UI components
- **Week 3**: Phase system and integration
- **Week 4**: Testing and documentation
- **Week 5**: Performance optimization
- **Week 6**: Release preparation

## Next Steps

1. Review and approve this plan
2. Create project scaffolding
3. Begin incremental migration
4. Maintain backward compatibility
5. Document breaking changes
6. Plan release strategy

## Prompt System Architecture

The prompt system is centralized in `prompts.py` with four main prompt pairs:

### Material Summary Prompts
- **Function**: `get_material_summary_prompt(source, content)`
- **System**: `MATERIAL_SUMMARY_SYSTEM`
- **Purpose**: Technical document analysis and structured data extraction
- **Output**: JSON with thinking, main_topic, technologies, key_concepts, microsoft_products, document_type, summary

### Directory Selection Prompts  
- **Function**: `get_directory_selection_prompt(config, repo_path, repo_structure, materials_info)`
- **System**: `DIRECTORY_SELECTION_SYSTEM`
- **Purpose**: Optimal directory selection based on repository structure and materials
- **Output**: JSON with thinking, working_directory, justification, confidence

### Content Strategy Prompts
- **Function**: `get_content_strategy_prompt(config, materials_summary, content_summary)`  
- **System**: `CONTENT_STRATEGY_SYSTEM`
- **Purpose**: Generate CREATE/UPDATE actions based on gap analysis
- **Output**: JSON with thinking, create_actions[], update_actions[], confidence, summary

### Content Type Selection Prompts
- **Function**: `get_content_type_selection_prompt(content_goal, filename, reason, materials_summary, content_types)`
- **System**: `CONTENT_TYPE_SELECTION_SYSTEM`
- **Purpose**: Select appropriate Microsoft documentation content type for new content
- **Output**: JSON with thinking, content_type, ms_topic, justification, confidence

All prompts enforce:
- Strict JSON format validation
- Mandatory planning process documentation in "thinking" field
- Detailed reasoning for all decisions
- No fabrication of information not in source 