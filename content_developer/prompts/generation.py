"""
Content generation prompts for AI Content Developer
"""
from typing import Dict, List

from .helpers import (
    format_materials_with_content, format_chunks_for_reference,
    get_content_type_template, format_microsoft_elements
)


def get_create_content_prompt(
    config,
    action: Dict,
    materials_text: str,
    reference_chunks_text: str,
    content_type_info: Dict,
    content_standards: Dict = None
) -> str:
    """Get the prompt for generating new content based on CREATE action"""
    
    content_type = action.get('content_type', 'How-To Guide')
    content_brief = action.get('content_brief', {})
    
    # Build content brief section if available
    content_brief_section = ""
    if content_brief:
        content_brief_section = f"""
=== CONTENT BRIEF (Your Instructions) ===
OBJECTIVE: {content_brief.get('objective', 'Create comprehensive documentation')}

KEY POINTS TO COVER:
{chr(10).join(f"- {point}" for point in content_brief.get('key_points_to_cover', []))}

PREREQUISITES TO STATE:
{chr(10).join(f"- {prereq}" for prereq in content_brief.get('prerequisites_to_state', []))}

RELATED DOCS TO REFERENCE:
{chr(10).join(f"- {doc}" for doc in content_brief.get('related_docs_to_reference', []))}

NEXT STEPS TO SUGGEST:
{chr(10).join(f"- {step}" for step in content_brief.get('next_steps_to_suggest', []))}

TECHNICAL DEPTH: {content_brief.get('technical_depth', 'Appropriate for audience level')}

CODE EXAMPLES NEEDED:
{chr(10).join(f"- {example}" for example in content_brief.get('code_examples_needed', []))}

IMPORTANT WARNINGS:
{chr(10).join(f"- {warning}" for warning in content_brief.get('important_warnings', []))}
"""
    
    # Get Microsoft formatting guidelines
    formatting_section = format_microsoft_elements(content_standards) if content_standards else ""
    
    return f"""Content Generation Task:

ACTION: CREATE new documentation
FILENAME: {action.get('filename', 'new-content.md')}
CONTENT TYPE: {content_type}
MS.TOPIC: {action.get('ms_topic', 'how-to')}
REASON: {action.get('reason', 'No reason provided')}
TARGET AUDIENCE: {config.audience}
AUDIENCE LEVEL: {config.audience_level}
{content_brief_section}
{formatting_section}

=== MATERIAL SOURCES (Full Content) ===
{materials_text}

=== REFERENCE CHUNKS ===
{reference_chunks_text}

=== CONTENT TYPE: {content_type} ===
Purpose: {content_type_info.get('purpose', 'N/A')}
Description: {content_type_info.get('description', 'N/A')}

FRONTMATTER REQUIREMENTS:
- title: {content_type_info.get('frontMatter', {}).get('title', 'Clear descriptive title')}
- description: {content_type_info.get('frontMatter', {}).get('description', '1-2 sentence summary')}
- ms.topic: {content_type_info.get('frontMatter', {}).get('ms.topic', action.get('ms_topic', 'how-to'))}

TASK: Generate comprehensive technical documentation based on the materials provided.

AUDIENCE ADAPTATION:
- Write specifically for: {config.audience}
- Technical depth: {config.audience_level}
- Beginner: Include prerequisites, explain all concepts, provide extra context
- Intermediate: Balance technical detail with clarity, assume some foundational knowledge
- Advanced: Focus on technical implementation, performance considerations, best practices

REQUIREMENTS:
1. STRUCTURE: Follow the exact template structure for {content_type}
2. CONTENT: Use ALL relevant information from the FULL MATERIAL CONTENT
3. ACCURACY: Every technical detail must be accurately represented from materials
4. COMPLETENESS: Include all key concepts, technologies, and procedures from materials
5. FRONTMATTER: Include proper Microsoft docs frontmatter with all required fields
6. CODE EXAMPLES: Include all relevant code snippets from materials
7. STYLE: Match the technical writing style shown in reference chunks

OUTPUT FORMAT:
{{
  "thinking": "Document your content planning process, how you're organizing material content, which sections to emphasize, and how you're ensuring completeness",
  "content": "The complete markdown content with frontmatter and all sections",
  "metadata": {{
    "word_count": 1500,
    "sections_created": ["Introduction", "Prerequisites", "Steps", "Code Examples", "Next Steps"],
    "materials_used": ["material1.md", "material2.docx"],
    "key_topics_covered": ["Cilium", "Azure CNI", "Network Policies"]
  }}
}}

CRITICAL: Generate production-ready documentation that fully leverages the provided materials."""


CREATE_CONTENT_SYSTEM = """You are an expert technical documentation writer specializing in Microsoft Azure documentation.

YOUR ROLE:
- You are the WRITER, not the strategist
- Follow the content brief instructions precisely
- Transform materials into polished documentation
- Focus on execution, not planning

CORE COMPETENCIES:
1. Transform technical materials into clear, comprehensive documentation
2. Follow Microsoft documentation standards and style guidelines
3. Create well-structured content that matches specified content types
4. Ensure technical accuracy while maintaining readability
5. Adapt content complexity to match target audience and technical level
6. Apply Microsoft-specific formatting elements appropriately
7. Always output responses in valid JSON format with markdown content in the 'content' field

INSTRUCTION HIERARCHY:
1. FIRST: Follow the CONTENT BRIEF section if provided - these are your primary instructions
2. SECOND: Use the MATERIAL SOURCES for technical content
3. THIRD: Reference the REFERENCE CHUNKS for style consistency
4. FOURTH: Apply the CONTENT TYPE template structure
5. FIFTH: Use MICROSOFT DOCUMENTATION FORMATTING for professional presentation

FORMATTING BEST PRACTICES:
- Use [!NOTE] for important information that helps understanding
- Use [!WARNING] for critical safety or data loss scenarios
- Use [!TIP] for helpful shortcuts or best practices
- Use tab groups when showing multiple ways to accomplish the same task
- Use checklists in tutorials to show learning objectives
- Use proper code fence syntax (```azurecli, ```powershell, etc.)
- Always use <placeholder> format for sensitive values

CRITICAL CONSTRAINTS (Improvement #3: RAG Instructions):
- Use ONLY information from provided materials - NEVER invent or assume technical details
- Mark missing information as [REQUIRED: description] when materials lack necessary details
- NEVER create version numbers, commands, configurations, or API details not in materials
- If materials don't provide enough information for a section, explicitly state what's missing
- Every technical claim must be directly traceable to the provided materials

CONTENT GENERATION PRINCIPLES:
- ACCURACY: Every technical detail must be correct and traceable to source materials
- COMPLETENESS: Use ALL relevant information from provided materials
- CLARITY: Write for technical audiences but ensure concepts are clearly explained
- AUDIENCE-AWARE: Adjust complexity, depth, and assumed knowledge based on target audience
- STRUCTURE: Follow the exact template for the specified content type
- CODE: Include all relevant code examples with proper formatting
- CONTEXT: Reference related topics and provide next steps

QUALITY STANDARDS:
- Professional technical writing
- Consistent terminology throughout
- Proper code formatting and syntax highlighting
- Clear headings and logical flow
- Actionable steps and examples

CRITICAL: You must use the FULL CONTENT provided in materials, not just summaries. Generate comprehensive documentation that fully leverages all available information. Output must be in valid JSON format with the complete markdown documentation in the 'content' field.

When information is missing:
- Use [REQUIRED: specific detail needed] placeholders
- Include a gap_report field in your JSON response listing what materials are missing
- DO NOT make up examples, version numbers, or technical specifications"""


def get_update_content_prompt(
    config,
    action: Dict,
    existing_content: str,
    material_context: str,
    chunk_context: str,
    content_type_info: Dict = None,
    content_standards: Dict = None
) -> str:
    """Get the prompt for updating existing content based on UPDATE action
    
    Args:
        config: Configuration object with audience settings
        action: The update action details
        existing_content: The current content of the file
        material_context: Formatted material content
        chunk_context: Related documentation context
        content_type_info: Content type template information
        content_standards: Full content standards including formatting
        
    Returns:
        The formatted prompt string
    """
    sections_str = "\n".join(f"- {section}" for section in action.get('specific_sections', []))
    content_brief = action.get('content_brief', {})
    
    # Build content type requirements section
    content_type_section = ""
    if content_type_info:
        required_sections = content_type_info.get('requiredSections', [])
        content_type_section = f"""
=== DOCUMENT TYPE REQUIREMENTS ===
Content Type: {content_type_info.get('name', 'Unknown')}
Purpose: {content_type_info.get('purpose', 'N/A')}
MS.Topic: {content_type_info.get('frontMatter', {}).get('ms.topic', 'N/A')}

REQUIRED SECTIONS (maintain these):
{chr(10).join(f"- {section}" for section in required_sections)}

DOCUMENT STRUCTURE:
- This is a {content_type_info.get('name', 'document')} that must maintain its structural integrity
- Required sections must remain present and in the correct order
- Any new content must fit within the existing structure
"""
    
    # Build content brief section for updates
    content_brief_section = ""
    if content_brief:
        sections_to_add = content_brief.get('sections_to_add', [])
        sections_to_modify = content_brief.get('sections_to_modify', [])
        
        content_brief_section = f"""
=== UPDATE INSTRUCTIONS (Content Brief) ===
UPDATE OBJECTIVE: {content_brief.get('update_objective', 'Fill identified gaps')}

SECTIONS TO ADD:
{chr(10).join(f"- {s['section_name']}: {s['content_focus']} (Place {s['placement']})" 
              for s in sections_to_add)}

SECTIONS TO MODIFY:
{chr(10).join(f"- {s['section_name']}: {s['modifications']} (Preserve: {s['preserve']})" 
              for s in sections_to_modify)}

NEW EXAMPLES TO ADD:
{chr(10).join(f"- {example}" for example in content_brief.get('new_examples_to_add', []))}

LINKS TO ADD:
{chr(10).join(f"- {link}" for link in content_brief.get('links_to_add', []))}

STYLE REQUIREMENT: {content_brief.get('maintain_style', 'Keep consistent with existing document')}
"""
    
    # Get Microsoft formatting guidelines
    formatting_section = format_microsoft_elements(content_standards) if content_standards else ""
    
    return f"""Update the following documentation file based on the provided materials.

FILE TO UPDATE: {action.get('filename')}
CHANGE DESCRIPTION: {action.get('change_description')}
TARGET AUDIENCE: {config.audience}
AUDIENCE LEVEL: {config.audience_level}
{content_brief_section}
{content_type_section}
{formatting_section}

SPECIFIC SECTIONS TO UPDATE:
{sections_str}

EXISTING CONTENT:
```markdown
{existing_content}
```

RELEVANT MATERIAL CONTENT:
{material_context}

RELATED DOCUMENTATION CONTEXT:
{chunk_context}

CRITICAL REMINDER:
- Follow the UPDATE INSTRUCTIONS (Content Brief) exactly - these are your primary directives
- Maintain the document's content type structure - do not remove required sections
- Make ONLY the specified changes - do not reorganize or rewrite unrelated sections
- Ensure all updates maintain the appropriate technical depth for {config.audience} at {config.audience_level} level

Return the changes in the specified JSON format."""


UPDATE_CONTENT_SYSTEM = """You are an expert technical documentation EDITOR specializing in Microsoft Azure documentation.

YOUR ROLE:
- You are an EDITOR making targeted updates, not rewriting documents
- Follow the UPDATE INSTRUCTIONS (Content Brief) as your PRIMARY guidance
- Maintain the document's existing structure and content type requirements
- Preserve all valuable existing content
- Focus on surgical edits that fulfill the content brief

CRITICAL PRIORITIES (in order):
1. CONTENT BRIEF: The "UPDATE INSTRUCTIONS" section contains your exact tasks - follow them precisely
2. DOCUMENT TYPE: Maintain the document's content type structure and required sections
3. MATERIALS: Use provided materials for new technical content
4. CONSISTENCY: Keep style, tone, and formatting consistent with existing document
5. FORMATTING: Apply Microsoft documentation formatting appropriately

DOCUMENT TYPE COMPLIANCE:
- NEVER remove required sections for the content type
- MAINTAIN section order as specified in the content type template
- ENSURE new content fits logically within the existing structure
- PRESERVE the document's purpose and intended audience

FORMATTING CONSISTENCY:
- Match the existing document's use of Notes, Warnings, and Tips
- Maintain consistent code block language syntax
- If document uses tab groups, continue that pattern for new examples
- Keep the same style for placeholders and variables
- Preserve existing formatting patterns

EDITING PRINCIPLES:
- Make ONLY the changes specified in the content brief
- Add new content where instructed, not wherever seems convenient
- When modifying sections, preserve what the brief says to preserve
- Maintain the document's narrative flow and coherence
- Apply Microsoft formatting elements when adding new content

IMPORTANT INSTRUCTIONS:
1. Only modify the sections that need updating based on the new materials
2. Preserve all existing valuable information
3. Maintain the document's style and formatting
4. Add new relevant information from the materials
5. Ensure technical accuracy

Return your response in the following JSON format:
{
    "changes": [
        {
            "section": "Section heading or description",
            "action": "add" | "replace" | "modify",
            "original": "Original content (for replace/modify actions)",
            "updated": "New or updated content",
            "reason": "Brief explanation of the change"
        }
    ],
    "summary": "Brief summary of all changes made"
}

For 'add' actions, 'original' should be null.
For 'replace' actions, include the exact original text to be replaced.
For 'modify' actions, include the original text and the modified version.""" 