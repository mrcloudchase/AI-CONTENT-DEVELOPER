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
    
    # Build section order information
    section_order_info = ""
    if content_type_info.get('sectionOrder'):
        section_order = content_type_info['sectionOrder']
        section_order_info = f"""
REQUIRED SECTION ORDER:
{chr(10).join(f"{s['position']}. {s['name']} {'(REQUIRED)' if s.get('required') else '(Optional)'} {'[TERMINAL - Must be last]' if s.get('terminal') else ''}" 
              for s in sorted(section_order, key=lambda x: x['position']))}
"""
    
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

{section_order_info}

TASK: Generate comprehensive technical documentation based on the materials provided.

CRITICAL SECTION ORDER RULES:
1. Follow the EXACT section order shown above
2. Include ALL required sections
3. Terminal sections (marked with [TERMINAL]) MUST be the last section
4. NEVER add any content after terminal sections
5. Optional sections should be included if relevant content exists in materials

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
  "thinking": "1. Content planning: Document your content planning process and material organization.\n2. Section development: How you're organizing material content into sections.\n3. Audience adaptation: How you're adapting content for the target audience.\n4. Technical accuracy: How you're ensuring all technical details are accurate.\n5. Completeness validation: How you're ensuring all key materials are included.",
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

CRITICAL TEMPLATE ENFORCEMENT RULES:

DOCUMENT STRUCTURE CONCEPT:
Every technical document follows a logical flow:
1. **Introduction/Context** - Sets up what the reader will learn
2. **Main Content** - The core information, procedures, or concepts
3. **Conclusion/Navigation** - Wraps up and guides readers to next steps

TERMINAL SECTIONS EXPLAINED:
Terminal sections are the FINAL sections that conclude the document and help readers navigate to related content. They:
- Summarize what was covered
- Suggest logical next steps in the learning journey
- Provide links to related documentation
- Offer additional resources for deeper learning

Think of them as the "exit doors" of your document - they help readers leave gracefully and know where to go next.

IDENTIFYING TERMINAL SECTIONS:
Terminal sections typically have names that indicate conclusion or navigation:
- Contains "Next" → suggests future actions (Next Steps, What's Next)
- Contains "Related" → links to related content (Related Articles, Related Documentation)
- Contains "See also", "Learn more", "Additional", "Further" → provides extra resources
- Contains "References", "Resources" → lists additional materials
- Contains "Conclusion", "Summary" → wraps up the content

SECTION ORDERING RULES:
1. ALWAYS start with introductory sections (Introduction, Overview, Prerequisites)
2. Place main content in the middle (procedures, concepts, examples)
3. ALWAYS end with terminal sections (Next Steps, Related content)
4. NEVER add content after terminal sections - they must be the last thing readers see
5. Terminal sections should feel like a natural conclusion, not an abrupt end

PLACEMENT PRINCIPLES:
- If the template shows a section with position 99, it's terminal
- If a section primarily contains links to other docs, it's likely terminal
- If a section tells readers what to do after this document, it's terminal
- When creating content, reserve the end for navigation and conclusion

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

STRUCTURAL INTEGRITY CHECK:
Before finalizing your content, verify:
□ Does the document follow the template's section order?
□ Are all required sections present?
□ Does the document flow from introduction → main content → conclusion?
□ Are terminal sections (Next Steps, Related content) at the very end?
□ Is there a clear narrative arc that guides the reader?

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
    template_enforcement_section = ""
    if content_type_info:
        required_sections = content_type_info.get('requiredSections', [])
        terminal_sections = content_type_info.get('terminalSections', [])
        
        content_type_section = f"""
=== DOCUMENT TYPE REQUIREMENTS ===
Content Type: {content_type_info.get('name', 'Unknown')}
Purpose: {content_type_info.get('purpose', 'N/A')}
MS.Topic: {content_type_info.get('frontMatter', {}).get('ms.topic', 'N/A')}

REQUIRED SECTIONS (maintain these):
{chr(10).join(f"- {section}" for section in required_sections)}

TERMINAL SECTIONS (must remain last):
{chr(10).join(f"- {section}" for section in terminal_sections)}

DOCUMENT STRUCTURE:
- This is a {content_type_info.get('name', 'document')} that must maintain its structural integrity
- Required sections must remain present and in the correct order
- Any new content must fit within the existing structure
- CRITICAL: No content may be added after terminal sections
"""
        
        # Add template enforcement rules
        if content_standards and 'templateEnforcementRules' in content_standards:
            rules = content_standards['templateEnforcementRules']
            template_enforcement_section = f"""
=== TEMPLATE ENFORCEMENT RULES ===
{chr(10).join(f"- {rule['rule']}: {rule['description']}" for rule in rules if rule.get('enforcement') == 'strict')}
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
{template_enforcement_section}
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

UPDATE TASK:
1. Read and understand the entire existing document
2. Follow the UPDATE INSTRUCTIONS (Content Brief) to make the requested changes
3. Integrate new information from the materials naturally
4. Preserve all valuable existing content
5. Return the COMPLETE updated document

OUTPUT FORMAT:
{{
  "thinking": "1. Document analysis: Explain your update strategy and understanding of existing content.\n2. Change identification: What specific changes you're making and where.\n3. Content integration: How you're placing new content while preserving existing value.\n4. Structure preservation: How you're maintaining document integrity and flow.\n5. Quality assurance: How you're ensuring the updated document meets all requirements.",
  "updated_document": "The COMPLETE updated markdown document with all changes integrated",
  "changes_summary": "Brief summary of what was updated",
  "metadata": {{
    "sections_modified": ["List of sections that were changed"],
    "sections_added": ["List of any new sections added"],
    "word_count_before": estimated_original_count,
    "word_count_after": estimated_new_count
  }}
}}

CRITICAL: Return the ENTIRE updated document in the 'updated_document' field, not just the changes."""


UPDATE_CONTENT_SYSTEM = """You are an expert technical documentation EDITOR specializing in Microsoft Azure documentation.

YOUR ROLE:
- You are an EDITOR making targeted updates to existing documentation
- Follow the UPDATE INSTRUCTIONS (Content Brief) as your PRIMARY guidance  
- Maintain the document's existing structure and valuable content
- Add new information from materials while preserving what works

CRITICAL PRIORITIES (in order):
1. CONTENT BRIEF: The "UPDATE INSTRUCTIONS" section contains your exact tasks - follow them precisely
2. PRESERVE VALUE: Keep all existing valuable content that doesn't need updating
3. MATERIALS: Integrate new technical content from provided materials seamlessly
4. CONSISTENCY: Maintain the document's style, tone, formatting, and flow
5. STRUCTURE: Respect the document's content type and section organization

EDITING APPROACH:
- Read and understand the ENTIRE existing document first
- Identify where updates are needed based on the content brief
- Make surgical edits - don't rewrite sections that don't need changes
- Blend new content naturally with existing content
- Ensure smooth transitions between existing and new content

DOCUMENT INTEGRITY:
- Preserve the document's narrative flow
- Keep all code examples, warnings, and tips that are still relevant
- Maintain heading hierarchy and structure
- Ensure frontmatter remains valid and complete
- Keep terminal sections (Next Steps, Related content) at the end

QUALITY CHECKLIST:
Before returning the updated document, verify:
□ Have I followed all instructions in the content brief?
□ Is all valuable existing content preserved?
□ Are new materials integrated naturally?
□ Does the document still flow logically?
□ Is the style consistent throughout?
□ Are terminal sections still at the end?

OUTPUT REQUIREMENTS:
Return the COMPLETE updated document that:
1. Incorporates all requested changes from the content brief
2. Integrates new information from materials
3. Preserves all valuable existing content
4. Maintains consistent style and formatting
5. Keeps proper document structure with terminal sections at the end

The goal is a seamless update where new content feels like it was always part of the document.""" 