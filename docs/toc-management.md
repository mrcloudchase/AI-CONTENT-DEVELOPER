# TOC Management in AI Content Developer

## Overview

Phase 4 of AI Content Developer automatically manages Table of Contents (TOC.yml) entries for newly created and updated documentation files. This ensures all documentation is properly indexed and accessible through the navigation structure.

## How It Works

1. **Reads existing TOC.yml**: The processor reads the current TOC structure
2. **Identifies missing entries**: Checks which created/updated files are not yet in the TOC
3. **Determines optimal placement**: Uses AI to analyze content types and find the best location
4. **Returns complete updated TOC**: The LLM returns the entire TOC.yml file with new entries integrated

## Key Features

### Intelligent Placement
The AI considers:
- **Content type** (How-To, Tutorial, Concept, Quickstart, etc.)
- **Topic relationships** with existing content
- **Directory structure** hints
- **Microsoft Learn conventions** for documentation organization

### Complete File Generation
Unlike earlier approaches that only returned fragments, the TOC processor now:
- Returns the **complete updated TOC.yml** file
- Preserves all existing entries exactly as they are
- Integrates new entries in appropriate locations
- Maintains proper YAML formatting and indentation

### Large TOC Support
For TOC files larger than 20KB:
- Automatically creates a condensed version for the AI prompt
- Preserves the full structure for reference
- Ensures accurate placement despite file size

## Usage

### Preview Mode (Default)
```bash
python main.py <args> --phases 1234
```
- Generates a preview of the updated TOC at `./llm_outputs/preview/toc/TOC_<directory>.yml`
- Does not modify the actual TOC.yml file
- Shows what changes would be made

### Apply Changes Mode
```bash
python main.py <args> --phases 1234 --apply-changes
```
- Applies all generated content to the repository
- Writes the complete updated TOC.yml file
- Replaces the existing TOC.yml with the AI-generated version

### Skip TOC Management
```bash
python main.py <args> --phases 123 --skip-toc
```
- Skips Phase 4 entirely
- Useful if TOC.yml has syntax errors or special formatting

## TOC Entry Format

The AI generates entries following this format:
```yaml
- name: Display Name
  href: relative/path/to/file.md
  items: # Optional, for nested structure
    - name: Nested Item
      href: path/to/nested.md
```

## Placement Guidelines

The AI follows these conventions:
- **Quickstarts**: Early in sections for quick wins
- **Concepts**: Before procedural content
- **How-to guides**: Main body of procedural sections
- **Tutorials**: Dedicated learning sections
- **Reference**: End of sections

## Error Handling

### YAML Syntax Errors
If the existing TOC.yml has syntax errors:
```
TOC.yml has invalid YAML syntax: while scanning a simple key...
```
**Solution**: Fix the YAML syntax manually or use `--skip-toc` flag

### File Size Truncation
Previously, files were truncated at 15,000 characters. This has been fixed to read the entire TOC.yml file.

### Missing TOC.yml
If no TOC.yml exists in the working directory:
```
TOC.yml not found in working directory
```
**Solution**: Create a basic TOC.yml or choose a different working directory

## Best Practices

1. **Review before applying**: Always review the TOC preview before using `--apply-changes`
2. **Backup important TOCs**: Keep a backup of complex TOC structures
3. **Test incrementally**: Add a few files at a time for large documentation sets
4. **Validate YAML**: Ensure your existing TOC.yml is valid YAML before running

## Example Output

When TOC management succeeds:
```
📑 TOC Management Results:
  • Status: TOC updated successfully
  • Changes Made: Yes
  • Applied to Repository: ✅ Yes
  • Entries Added (2):
    - integrate-cilium-aks.md
    - configure-cilium-endpoints.md
  • TOC Preview: ./llm_outputs/preview/toc/TOC_aks.yml
```

## Technical Details

### Model Requirements
- Uses models that support JSON response format (e.g., gpt-4o)
- Falls back to manual JSON parsing if needed
- Configurable via `OPENAI_TOC_MODEL` environment variable

### File Processing
- Reads entire TOC.yml without truncation (`limit=None`)
- Handles large files by condensing for AI prompt
- Preserves exact formatting of existing entries 