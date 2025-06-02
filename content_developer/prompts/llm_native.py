"""
LLM-Native prompts for intelligent document processing
"""

import json

# Document Structure Analysis
DOCUMENT_STRUCTURE_SYSTEM = """You are an expert at understanding document structure and organization.
You understand:
- Document flow from introduction to conclusion
- Section hierarchies and relationships
- Terminal sections that conclude documents
- Content organization patterns

CRITICAL: You MUST follow JSON type specifications exactly. When a field specifies STRING, never return an array/list. When a field specifies LIST/ARRAY, never return a string."""

def get_document_structure_prompt(content: str) -> str:
    """Get prompt for analyzing document structure"""
    return f"""Analyze this document's structure and provide insights:

{content}

IMPORTANT CONTEXT:
- If this appears to be a file/directory tree, analyze it as a repository structure
- Top-level folders (like 'articles/') contain service-specific subdirectories
- Service directories (like 'aks/', 'azure-arc/') contain feature subdirectories
- Look for patterns in organization (e.g., concepts/, how-to/, reference/)

Return a JSON response with EXACTLY these fields and types:
{{
    "thinking": "Your step-by-step analysis process. Use numbered steps:\n1. First observation...\n2. Pattern identification...\n3. Conclusion...",  // STRING with numbered steps
    "sections": ["array", "of", "section", "names"],  // LIST of strings
    "terminal_sections": ["array", "of", "terminal", "section", "names"],  // LIST of strings
    "content_flow": "A single descriptive string about document flow",  // STRING (not array)
    "key_topics": ["array", "of", "main", "topics"]  // LIST of strings
}}

For repository structures:
- "thinking" should explain how you identified the structure pattern using numbered steps (1., 2., 3., etc.)
- "sections" should list main service/topic directories (e.g., ["aks", "azure-arc", "container-registry"])
- "terminal_sections" should list non-content items (e.g., ["README.md", "LICENSE", "media/", "includes/"])
- "content_flow" should describe the organizational hierarchy
- "key_topics" should list the main Azure services or technologies covered

CRITICAL TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- sections: MUST be an array/list of strings
- terminal_sections: MUST be an array/list of strings  
- content_flow: MUST be a single string (NOT an array)
- key_topics: MUST be an array/list of strings

Example response for a repository:
{{
    "thinking": "1. I analyzed the repository structure and identified a service-based organization pattern.\n2. The 'articles' directory contains subdirectories for different Azure services like aks, azure-arc, and container-registry.\n3. Each service directory has its own documentation structure with concepts, how-to guides, and reference materials.\n4. I also noted terminal items like README.md and media folders that aren't content directories.",
    "sections": ["aks", "azure-arc", "container-registry", "azure-linux"],
    "terminal_sections": ["README.md", "LICENSE", "media", "includes"],
    "content_flow": "Repository organized by Azure service with each service having subdirectories for concepts, how-to guides, tutorials, and reference documentation",
    "key_topics": ["Azure Kubernetes Service", "Azure Arc", "Container Registry", "Azure Linux"]
}}"""

# Content Placement
CONTENT_PLACEMENT_SYSTEM = """You are an expert at document organization and content placement.
You understand:
- Logical flow of technical documentation
- Where different types of content belong
- Terminal sections must remain at the end
- Content should enhance document coherence

CRITICAL: You MUST follow JSON type specifications exactly. When a field specifies STRING, never return an array/list. When a field specifies LIST/ARRAY, never return a string."""

def get_content_placement_prompt(document: str, new_content_description: str, content_type: str = None) -> str:
    """Get prompt for suggesting content placement"""
    content_type_info = f"\nCONTENT TYPE: {content_type}" if content_type else ""
    
    return f"""I need to add new content to this document:

EXISTING DOCUMENT:
{document}

NEW CONTENT TO ADD:
{new_content_description}
{content_type_info}

Where should this content be placed? Consider:
1. Logical flow and reader experience
2. Related existing sections
3. Terminal sections must stay at the end

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered analysis steps:\n1. Document structure analysis...\n2. Content relationship evaluation...\n3. Placement decision...",  // STRING with numbered steps
    "recommended_placement": "Section name after which to add content",  // STRING
    "alternative_placements": ["array", "of", "other", "valid", "options"],  // LIST of strings
    "creates_new_section": true/false,  // BOOLEAN
    "new_section_name": "Name if creating new section or null"  // STRING or null
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- recommended_placement: MUST be a string
- alternative_placements: MUST be an array/list of strings
- creates_new_section: MUST be a boolean (true/false)
- new_section_name: MUST be a string or null"""

# Terminal Section Detection
TERMINAL_SECTION_SYSTEM = """You are an expert at understanding document structure.
Terminal sections are those that conclude a document and guide readers to next steps.
Examples include: Next Steps, Related Documentation, See Also, Conclusion, References.

CRITICAL: You MUST follow JSON type specifications exactly. Return booleans as true/false, not strings."""

def get_terminal_section_prompt(section_title: str) -> str:
    """Get prompt for detecting terminal sections"""
    return f"""Is '{section_title}' a terminal section (a section that typically comes at the end of documentation)?

Terminal sections are like "exit doors" - once you reach them, you're leaving the main content. Examples:
- "What's Next?" / "Next Steps" - Leading readers elsewhere
- "Related Documentation" / "See Also" - External references  
- "Additional Resources" / "Further Reading" - Supplementary materials
- "References" / "Links" - Citation sections

Consider the semantic meaning, not just exact words. 

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered reasoning steps:\n1. Section title analysis...\n2. Pattern matching...\n3. Final determination...",  // STRING with numbered steps
    "is_terminal": true/false,  // BOOLEAN
    "pattern_matched": "Which terminal pattern it matches, or null"  // STRING or null
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- is_terminal: MUST be a boolean (true/false)
- pattern_matched: MUST be a string or null"""

# Content Quality Analysis
def get_content_quality_system(content_type: str) -> str:
    """Get system prompt for content quality analysis"""
    return f"""You are an expert at evaluating technical documentation quality.
You're analyzing a {content_type} document for:
- Completeness of required sections
- Clarity and organization
- Technical accuracy indicators
- Audience appropriateness

CRITICAL: You MUST follow JSON type specifications exactly. Numbers must be actual numbers, not strings."""

def get_content_quality_prompt(content: str, content_type: str = None) -> str:
    """Get prompt for analyzing content quality"""
    type_context = f"\nContent Type: {content_type}" if content_type else ""
    
    return f"""Analyze the quality of this content:{type_context}

{content}

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered analysis steps:\n1. Content structure review...\n2. Clarity assessment...\n3. Completeness check...\n4. Overall evaluation...",  // STRING with numbered steps
    "clarity_score": 0-10,  // NUMBER
    "completeness_score": 0-10,  // NUMBER  
    "accuracy_indicators": ["list", "of", "accuracy", "signals"],  // LIST of strings
    "improvement_areas": ["list", "of", "areas", "to", "improve"],  // LIST of strings
    "strengths": ["list", "of", "content", "strengths"]  // LIST of strings
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- clarity_score: MUST be a number between 0-10
- completeness_score: MUST be a number between 0-10
- accuracy_indicators: MUST be an array/list of strings
- improvement_areas: MUST be an array/list of strings
- strengths: MUST be an array/list of strings"""

# Information Extraction
INFORMATION_EXTRACTION_SYSTEM = """You are an expert at extracting structured information from documents.
You can identify and extract key concepts, technical details, and relationships.

CRITICAL: You MUST follow JSON type specifications exactly. Always return the requested structure with correct types."""

def get_information_extraction_prompt(content: str, extraction_purpose: str, expected_format: dict = None) -> str:
    """Get prompt for extracting specific information"""
    # Special handling for directory validation
    if "directory" in extraction_purpose.lower() and "validate" in extraction_purpose.lower():
        return f"""Extract information for: {extraction_purpose}

From this content:
{content}

VALIDATION APPROACH:
- Understand the repository's organizational pattern
- Evaluate if the selected directory fits that pattern
- Consider practical constraints (what directories actually exist)
- Validate the reasoning, not rigid rules

Return a JSON response with:
{{
    "thinking": "Your numbered validation steps:\n1. Repository structure analysis...\n2. Directory pattern evaluation...\n3. Practical constraints check...\n4. Final validation decision...",  // STRING with numbered steps
    "is_valid": true/false,  // BOOLEAN - is the selection reasonable given available options?
    "is_documentation_directory": true/false,  // BOOLEAN - is it for docs (not media/assets)?
    "pattern_match": "How well does selection fit the repository pattern",  // STRING
    "reason": "Explanation of validation result",  // STRING
    "concerns": ["array", "of", "any", "concerns"],  // LIST of strings or empty
    "suggested_alternative": "Better directory path only if current is clearly wrong"  // STRING or null
}}

VALIDATION PRINCIPLES:
- Accept practical decisions when ideal options don't exist
- Media/assets/includes directories are NOT valid for documentation
- If no perfect match exists, a general directory is acceptable
- Consider the repository's actual structure, not theoretical ideals
- Only suggest alternatives if they actually exist and are clearly better

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- is_valid: MUST be a boolean (true/false)
- is_documentation_directory: MUST be a boolean
- pattern_match: MUST be a string
- reason: MUST be a string
- concerns: MUST be an array/list of strings (can be empty)
- suggested_alternative: MUST be a string or null"""
    
    # Default extraction with format support
    if expected_format:
        # If format is provided, include thinking in the format
        if "thinking" not in expected_format:
            expected_format = {"thinking": "Your numbered extraction steps:\n1. Content analysis...\n2. Information identification...\n3. Data extraction...", **expected_format}
        format_spec = f"\nReturn JSON matching this structure:\n{json.dumps(expected_format, indent=2)}"
    else:
        format_spec = """
Return extracted information as JSON with a 'thinking' field containing numbered steps (1., 2., 3., etc.) explaining your extraction process."""
    
    return f"""Extract information for: {extraction_purpose}

Content:
{content}
{format_spec}"""

# TOC Placement
TOC_PLACEMENT_SYSTEM = """You are an expert at organizing documentation tables of contents.
You understand:
- Logical grouping of related topics
- Progressive complexity ordering
- Common documentation patterns
- User navigation needs

CRITICAL: You MUST follow JSON type specifications exactly. Arrays must contain objects with the exact structure specified."""

def get_toc_placement_prompt(toc_structure: str, new_entries: list) -> str:
    """Get prompt for TOC placement suggestions"""
    entries_description = "\n".join([
        f"- {entry['filename']}: {entry.get('description', 'No description')}"
        for entry in new_entries
    ])
    
    return f"""Where should these new documentation entries be placed in the TOC?

NEW ENTRIES:
{entries_description}

CURRENT TOC STRUCTURE:
{toc_structure}

Consider:
1. Logical grouping with related content
2. Progressive learning path
3. Existing organizational patterns

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered analysis steps:\n1. TOC structure understanding...\n2. Entry categorization...\n3. Placement logic...\n4. Final recommendations...",  // STRING with numbered steps
    "placements": [
        {{
            "filename": "example.md",  // STRING
            "suggested_location": "After 'Getting Started' section",  // STRING
            "parent_section": "Networking",  // STRING
            "reasoning": "Why this placement makes sense"  // STRING
        }}
    ],  // ARRAY of objects
    "toc_suggestions": ["array", "of", "improvement", "suggestions"]  // LIST of strings
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- placements: MUST be an array of objects, each with filename, suggested_location, parent_section, and reasoning (all strings)
- toc_suggestions: MUST be an array/list of strings"""

# Content Intent Understanding
CONTENT_INTENT_SYSTEM = """You are an expert at understanding documentation needs and intent.
You can analyze materials and goals to determine:
- What type of content is needed
- Target audience and their needs
- Key topics to cover
- Appropriate depth and style

CRITICAL: You MUST follow JSON type specifications exactly. Lists must be arrays, not strings."""

def get_content_intent_prompt(materials: str, goal: str) -> str:
    """Get prompt for understanding content intent"""
    return f"""Based on these materials and goal, what is the primary intent?

MATERIALS:
{materials}

GOAL: {goal}

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered analysis steps:\n1. Materials review...\n2. Goal analysis...\n3. Intent determination...\n4. Strategy formulation...",  // STRING with numbered steps
    "primary_intent": "Main purpose of the content",  // STRING
    "content_type": "Type of content to create",  // STRING
    "target_audience": "Who this is for",  // STRING
    "key_objectives": ["list", "of", "main", "objectives"],  // LIST of strings
    "success_criteria": ["how", "to", "measure", "success"]  // LIST of strings
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- primary_intent: MUST be a string
- content_type: MUST be a string
- target_audience: MUST be a string
- key_objectives: MUST be an array/list of strings
- success_criteria: MUST be an array/list of strings"""

# Chunk Ranking
CHUNK_RANKING_SYSTEM = """You are an expert at identifying relevant documentation.

CRITICAL: You MUST follow JSON type specifications exactly. The ranked_indices must be an array of numbers."""

def get_chunk_ranking_prompt(goal: str, chunks_list: str) -> str:
    """Get prompt for ranking content chunks"""
    return f"""Rank these content chunks by relevance to the goal.

GOAL: {goal}

CHUNKS TO RANK:
{chunks_list}

Return JSON with EXACTLY these fields and types:
{{
    "thinking": "Your numbered ranking process:\n1. Goal understanding...\n2. Chunk evaluation criteria...\n3. Relevance assessment...\n4. Final ranking logic...",  // STRING with numbered steps
    "rankings": [
        {{
            "chunk_id": "ID of the chunk",  // STRING
            "relevance_score": 0-10,  // NUMBER
            "relevance_reason": "Why this chunk is relevant"  // STRING
        }}
    ],
    "top_chunks": ["ordered", "list", "of", "most", "relevant", "chunk", "ids"],  // LIST of strings
    "key_themes": ["main", "themes", "found", "across", "chunks"]  // LIST of strings
}}

TYPE REQUIREMENTS:
- thinking: MUST be a string with numbered steps (1., 2., 3., etc.)
- rankings: MUST be an array of objects with chunk_id (string), relevance_score (number), and relevance_reason (string)
- top_chunks: MUST be an array/list of strings
- key_themes: MUST be an array/list of strings""" 