# Prompt Output Verification Report

This document verifies that all prompts from the prompt-chaining.md are outputting to the correct phase/step directories.

## Summary

All prompts are now correctly configured to output to their appropriate phase/step directories in `./llm_outputs/`.

## Phase/Step Directory Structure

### Phase 1: Repository Analysis
- **step-01**: Material Processing
  - ✅ Material Analysis prompts saved to `./llm_outputs/phase-01/step-01/`
- **step-02**: Directory Detection  
  - ✅ Repository Structure Analysis saved to `./llm_outputs/phase-01/step-02/`
  - ✅ Working Directory Selection saved to `./llm_outputs/phase-01/step-02/`
  - ✅ Directory Validation (Information Extraction) saved to `./llm_outputs/phase-01/step-02/`

### Phase 2: Content Strategy
- **step-01**: Content Discovery
  - ✅ Uses SmartChunker (non-LLM processing, no prompts saved)
- **step-02**: Strategy Generation
  - ✅ Content Intent Analysis saved to `./llm_outputs/phase-02/step-02/`
  - ✅ Chunk Ranking saved to `./llm_outputs/phase-02/step-02/`
  - ✅ Strategy Generation saved to `./llm_outputs/phase-02/step-02/`

### Phase 3: Content Generation
- **step-01**: Main orchestration (no direct LLM calls)
- **step-04**: CREATE Content
  - ✅ Content Creation prompts saved to `./llm_outputs/phase-03/step-04/`
- **step-05**: UPDATE Content
  - ✅ Content Update prompts will save to `./llm_outputs/phase-03/step-05/` (when updates occur)

### Phase 4: TOC Management
- **step-01**: TOC Processing
  - ✅ TOC Placement Analysis saved to `./llm_outputs/phase-04/step-01/`
  - ✅ TOC Generation saved to `./llm_outputs/phase-04/step-01/` (after fix)

## Issues Fixed

1. **TOC Generation** - Removed redundant `save_interaction` call that was hardcoding output to `./llm_outputs/toc_management/`. The `_call_llm` method already saves interactions automatically using the phase/step directory.

## How It Works

1. Each processor inherits from `SmartProcessor` which tracks `current_phase` and `current_step`
2. The orchestrator calls `set_phase_step(phase, step)` before processing
3. When `_call_llm` or `llm_call` is invoked with an `operation_name`, it automatically:
   - Determines the output directory using `_determine_phase_step_directory()`
   - Saves both prompt (.txt) and response (.json) files
   - Uses timestamp and sanitized operation name for filenames

## Verification Commands

To verify the directory structure:
```bash
# List all phase directories
find ./llm_outputs -type d -name "phase-*" | sort

# Check Phase 1 outputs
ls ./llm_outputs/phase-01/step-01/  # Material Analysis
ls ./llm_outputs/phase-01/step-02/  # Directory Detection & Validation

# Check Phase 2 outputs  
ls ./llm_outputs/phase-02/step-02/  # Strategy Generation

# Check Phase 3 outputs
ls ./llm_outputs/phase-03/step-04/  # CREATE Content

# Check Phase 4 outputs
ls ./llm_outputs/phase-04/step-01/  # TOC Management
```

## Additional Notes

- Material Sufficiency Check and Gap Analysis in `BaseContentProcessor` inherit the phase/step from their parent processors
- Any LLM calls without `operation_name` will not be saved
- The old directory structure (e.g., `./llm_outputs/toc_management/`) is maintained as a fallback when phase/step is not set 