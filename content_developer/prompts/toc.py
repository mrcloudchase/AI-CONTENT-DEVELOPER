"""
TOC (Table of Contents) management prompts
"""
from typing import List, Dict


def get_toc_update_prompt(
    existing_toc: str,
    missing_created_files: List[str],
    missing_updated_files: List[str],
    file_descriptions: Dict[str, Dict]
) -> str:
    """Generate prompt for updating TOC.yml"""
    
    # Build file context
    created_context = ""
    if missing_created_files:
        created_context = "\n=== NEWLY CREATED FILES (Need TOC entries) ===\n"
        for filepath in missing_created_files:
            desc = file_descriptions.get(filepath, {})
            created_context += f"\nFile: {filepath}\n"
            created_context += f"Content Type: {desc.get('content_type', 'Unknown')}\n"
            created_context += f"Purpose: {desc.get('reason', 'No description available')}\n"
            
            # Add directory hint if available
            if 'directory_hint' in desc:
                created_context += f"Location Hint: {desc['directory_hint']}\n"
            
            # Add content brief info if available
            brief = desc.get('content_brief', {})
            if brief.get('objective'):
                created_context += f"Objective: {brief['objective']}\n"
    
    updated_context = ""
    if missing_updated_files:
        updated_context = "\n=== UPDATED FILES (Missing from TOC) ===\n"
        for filepath in missing_updated_files:
            desc = file_descriptions.get(filepath, {})
            updated_context += f"\nFile: {filepath}\n"
            updated_context += f"Content Type: {desc.get('content_type', 'Unknown')}\n"
            updated_context += f"Changes: {desc.get('reason', 'File was updated')}\n"
    
    # Check if TOC was condensed
    toc_note = ""
    if "... [TOC continues with more entries] ..." in existing_toc:
        toc_note = """
NOTE: The TOC shown below has been condensed due to its large size. 
The actual TOC has many more entries between the sections shown.
Please focus on the overall structure and place new entries appropriately.
"""
    
    return f"""Update the TOC.yml file to include proper entries for new and updated documentation files.

{toc_note}
CURRENT TOC.yml:
```yaml
{existing_toc}
```

{created_context}
{updated_context}

TASK: Create a complete updated TOC.yml file that includes all existing entries PLUS the new entries for the missing files. The output should be the ENTIRE TOC.yml content that can be written directly to replace the current file.

REQUIREMENTS:
1. Return the COMPLETE TOC.yml file content (not just new entries)
2. Preserve ALL existing TOC entries exactly as they are
3. Add new entries in appropriate locations based on content type and topic
4. Use proper YAML formatting with correct indentation
5. Ensure all file paths are relative and correct
6. Add meaningful display names that match the document titles
7. Group related content together logically
8. Maintain alphabetical or logical ordering within sections

TOC ENTRY FORMAT:
- name: Display Name
  href: relative/path/to/file.md
  items: # Optional, for nested structure
    - name: Nested Item
      href: path/to/nested.md

PLACEMENT GUIDELINES:
- How-to guides: Place with other procedural content
- Concepts: Group with architectural/conceptual docs
- Quickstarts: Place at the beginning of relevant sections
- Tutorials: Group with learning materials
- Overview: Typically first in a section

IMPORTANT: Return the ENTIRE updated TOC.yml file content, not just the sections with changes. The 'content' field should contain the complete TOC.yml that will replace the existing file.

OUTPUT FORMAT:
{{
  "thinking": "1. Structure analysis: Explain your reasoning for placement decisions.\n2. Content categorization: How you categorized the new files.\n3. Placement strategy: Where and why you placed each entry.\n4. Integration approach: How you're maintaining the existing structure.\n5. Validation: Confirm the complete TOC maintains logical flow.",
  "content": "<COMPLETE updated TOC.yml content from first line to last line>",
  "entries_added": ["file1.md", "file2.md"],
  "entries_verified": ["existing1.md", "existing2.md"],
  "placement_decisions": {{
    "file1.md": "Placed under 'Getting Started' because it's a quickstart guide",
    "file2.md": "Added to 'Configuration' section with other how-to guides"
  }}
}}"""


TOC_UPDATE_SYSTEM = """You are an expert documentation architect specializing in Microsoft Learn documentation structure and navigation.

YOUR ROLE:
- Analyze existing TOC.yml structure
- Identify optimal placement for new documentation
- Integrate new entries into the complete TOC structure
- Return the ENTIRE updated TOC.yml file content

CRITICAL INSTRUCTION:
You must return the COMPLETE TOC.yml file with all existing entries preserved and new entries added in appropriate locations. The output should be ready to directly replace the existing TOC.yml file.

CORE COMPETENCIES:
1. Understanding documentation hierarchies and relationships
2. Creating intuitive navigation structures
3. Maintaining consistency in TOC organization
4. Following Microsoft Learn TOC conventions
5. Balancing depth vs. breadth in navigation trees

TOC STRUCTURE PRINCIPLES:
1. **Logical Grouping**: Related content should be grouped together
2. **Progressive Disclosure**: Start with overview/conceptual, then how-to, then reference
3. **Task-Oriented**: Organize around user tasks and goals
4. **Consistent Depth**: Avoid too many nesting levels (max 3-4)
5. **Meaningful Names**: Use clear, action-oriented names for entries

MICROSOFT LEARN TOC CONVENTIONS:
- Use sentence case for display names
- Keep names concise but descriptive
- Action-oriented names for how-to content
- Noun-based names for conceptual content
- Avoid redundancy with parent sections

PLACEMENT STRATEGY:
1. **Analyze Content Type**:
   - Quickstarts → Early in section for quick wins
   - Concepts → Before procedural content
   - How-to → Main body of procedural sections
   - Tutorials → Dedicated learning sections
   - Reference → End of sections

2. **Consider User Journey**:
   - What would users need to know first?
   - What's the logical progression?
   - How do topics build on each other?

3. **Maintain Patterns**:
   - Look for existing patterns in the TOC
   - Follow established grouping conventions
   - Keep similar content types together

YAML FORMATTING RULES:
- Use 2 spaces for indentation (not tabs)
- Lists start with hyphen + space
- No trailing spaces
- Proper nesting for hierarchical structure
- Quote strings with special characters

QUALITY CHECKS:
Before finalizing:
□ All new files have entries
□ Paths are relative and correct
□ Display names are meaningful
□ Structure is balanced (not too deep/shallow)
□ Related content is grouped
□ Ordering makes logical sense
□ YAML syntax is valid
□ Complete TOC is returned (not fragments)

COMMON PATTERNS:
```yaml
# Overview/Introduction section
- name: Overview
  href: overview.md
  items:
    - name: What is X
      href: what-is-x.md
    - name: Architecture
      href: architecture.md

# Getting Started section
- name: Get started
  items:
    - name: Quickstart
      href: quickstart.md
    - name: Tutorial
      href: tutorial.md

# How-to section
- name: How-to guides
  items:
    - name: Configure X
      href: configure-x.md
    - name: Manage Y
      href: manage-y.md

# Reference section
- name: Reference
  items:
    - name: API reference
      href: api-reference.md
```

Remember: 
1. The TOC is often the first thing users see. Make it intuitive, logical, and helpful for navigation.
2. ALWAYS return the complete TOC.yml file content, not just the modified sections.""" 