"""
Content generation prompts for AI Content Developer
"""
from typing import Dict, List

from .helpers import (
    format_materials_with_content, format_chunks_for_reference,
    get_content_type_template
)


def get_create_content_prompt(
    action: Dict,
    materials_text: str,
    reference_chunks_text: str,
    content_type_info: Dict
) -> str:
    """Get the prompt for generating new content based on CREATE action"""
    
    content_type = action.get('content_type', 'How-To Guide')
    
    return f"""Content Generation Task:

ACTION: CREATE new documentation
FILENAME: {action.get('filename', 'new-content.md')}
CONTENT TYPE: {content_type}
MS.TOPIC: {action.get('ms_topic', 'how-to')}
REASON: {action.get('reason', 'No reason provided')}

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

CORE COMPETENCIES:
1. Transform technical materials into clear, comprehensive documentation
2. Follow Microsoft documentation standards and style guidelines
3. Create well-structured content that matches specified content types
4. Ensure technical accuracy while maintaining readability
5. Always output responses in valid JSON format with markdown content in the 'content' field

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
    action: Dict,
    existing_content: str,
    material_context: str,
    chunk_context: str
) -> str:
    """Get the prompt for updating existing content based on UPDATE action
    
    Args:
        action: The update action details
        existing_content: The current content of the file
        material_context: Formatted material content
        chunk_context: Related documentation context
        
    Returns:
        The formatted prompt string
    """
    sections_str = "\n".join(f"- {section}" for section in action.get('specific_sections', []))
    
    return f"""Update the following documentation file based on the provided materials.

FILE TO UPDATE: {action.get('filename')}
CHANGE DESCRIPTION: {action.get('change_description')}

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

Please analyze the existing content and provide specific changes based on the new materials.
Focus on the sections mentioned above, but also identify any other sections that would benefit from updates based on the new information.
Return the changes in the specified JSON format."""


UPDATE_CONTENT_SYSTEM = """You are an expert technical writer tasked with updating specific sections of existing documentation.

Your goal is to make targeted updates while preserving the existing document structure and content.

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