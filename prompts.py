"""
Prompts for AI Content Developer
Centralized location for all LLM prompts used in Phase 1 and Phase 2
"""

from typing import List, Dict

# === MATERIAL PROCESSOR PROMPTS ===

def get_material_summary_prompt(source: str, content: str) -> str:
    """Get the prompt for technical document analysis and summarization"""
    return f"""Technical Document Analysis Task:

SOURCE: {source}

CONTENT TO ANALYZE:
{content[:12000]}

TASK: Perform comprehensive technical document analysis with structured data extraction.

MANDATORY PLANNING PROCESS:
1. READ: Systematically examine the entire content for technical details
2. CATEGORIZE: Determine document type and primary subject matter
3. EXTRACT: Identify all technologies, tools, concepts, and Microsoft products mentioned
4. VALIDATE: Verify all extracted information exists in the source content
5. SYNTHESIZE: Create comprehensive summary of purpose, scope, and technical value
6. STRUCTURE: Format findings into exact JSON specification

CRITICAL EXTRACTION REQUIREMENTS:
- technologies: Array of ALL technical tools, frameworks, services mentioned
- key_concepts: Array of ALL important concepts, methodologies, approaches
- microsoft_products: Array of ALL Microsoft/Azure products, services, tools
- main_topic: Single primary subject (e.g., "Azure CNI Networking", "Kubernetes Security")
- document_type: Specific type (e.g., "Technical Guide", "API Documentation", "Tutorial")
- summary: Comprehensive overview (100-200 words covering purpose, scope, key insights)

EXAMPLE OUTPUT FORMAT:
{{
  "thinking": "I systematically analyzed the Azure CNI documentation. First, I identified this as a technical implementation guide focused on container networking. I extracted specific technologies: Azure CNI, Cilium, Kubernetes, eBPF. Key concepts include endpoint slices, network policies, automatic configuration. Microsoft products mentioned are AKS, Azure Virtual Network, Azure Resource Manager. The document provides comprehensive coverage of advanced networking configuration with specific implementation examples.",
  "main_topic": "Azure CNI Cilium Integration",
  "technologies": ["Azure CNI", "Cilium", "Kubernetes", "eBPF", "CiliumEndpointSlices"],
  "key_concepts": ["network policies", "endpoint slices", "automatic configuration", "container networking"],
  "microsoft_products": ["Azure Kubernetes Service", "Azure Virtual Network", "Azure Resource Manager"],
  "document_type": "Technical Implementation Guide",
  "summary": "Comprehensive guide covering Azure CNI integration with Cilium for advanced Kubernetes networking. Details automatic configuration of CiliumEndpointSlices, network policy implementation, and eBPF-based networking optimization. Provides specific configuration examples, troubleshooting steps, and best practices for production deployment in Azure Kubernetes Service environments.",
  "source": "{source}"
}}

YOU MUST RETURN EXACTLY THIS JSON FORMAT. NO DEVIATIONS ALLOWED."""

MATERIAL_SUMMARY_SYSTEM = """You are a specialized technical document analyzer with expertise in cloud technologies, containerization, and Microsoft Azure services.

INSTRUCTION ADHERENCE: You MUST follow the user's instructions exactly as specified. GPT-4.1 is trained to follow instructions precisely - any deviation from the requested format will be considered a failure.

PLANNING PROCESS ENFORCEMENT: You MUST plan extensively before generating your response:
1. Carefully read through the entire content multiple times
2. Identify document type and primary technical focus
3. Extract ALL mentioned technologies, tools, and frameworks
4. Extract ALL key concepts, methodologies, and approaches  
5. Extract ALL Microsoft/Azure products and services
6. Document your complete analysis process in the thinking field
7. Create comprehensive summary covering purpose, scope, and technical value

JSON FORMAT ENFORCEMENT:
- thinking: MUST document complete step-by-step analysis process (minimum 100 words)
- main_topic: MUST be concise primary subject (maximum 50 characters)
- technologies: MUST be complete array of technical tools/frameworks mentioned
- key_concepts: MUST be complete array of important concepts covered
- microsoft_products: MUST be complete array of Microsoft/Azure products mentioned
- document_type: MUST be specific document classification
- summary: MUST be comprehensive overview (100-200 words)
- source: MUST exactly match provided source path

VALIDATION CHECKLIST:
✓ thinking field documents complete analysis methodology
✓ main_topic is concise and specific
✓ technologies array includes ALL technical tools mentioned
✓ key_concepts array includes ALL important concepts
✓ microsoft_products array includes ALL Microsoft/Azure references
✓ document_type is specific classification
✓ summary is comprehensive 100-200 word overview
✓ source exactly matches input
✓ All arrays contain relevant items (empty arrays only if nothing found)

CRITICAL: You MUST NOT fabricate information not present in the source content. Extract only what is explicitly mentioned. Return only valid JSON matching the exact format provided."""

# === DIRECTORY DETECTOR PROMPTS ===

def get_directory_selection_prompt(config, repo_path: str, repo_structure: str, materials_info: str) -> str:
    """Get the prompt for optimal directory selection"""
    return f"""Directory Selection Analysis Task:

CONTENT GOAL: {config.content_goal}
SERVICE AREA: {config.service_area}

REPOSITORY: {repo_path}

REPOSITORY STRUCTURE:
{repo_structure}

MATERIALS CONTEXT:
{materials_info}

TASK: Select the optimal directory for content placement based on comprehensive analysis.

MANDATORY PLANNING PROCESS:
1. ANALYZE: Systematically examine the repository structure to understand organizational patterns
2. CONTEXTUALIZE: Review materials context to identify key technologies, concepts, and products  
3. MATCH: Identify 2-3 candidate directories that align with content goal and service area
4. VERIFY: Ensure selected directory exists exactly as written in the provided structure
5. DECIDE: Select EXACTLY ONE directory with detailed justification
6. ASSESS: Evaluate confidence based on alignment quality and materials relevance

CRITICAL SELECTION REQUIREMENTS:
- working_directory MUST be exact path from repository structure (no modifications)
- justification MUST explain WHY this directory is optimal (minimum 50 characters)
- thinking MUST document complete analysis process showing all evaluation steps
- confidence MUST be float between 0.0-1.0 reflecting selection certainty

EXAMPLE OUTPUT FORMAT:
{{
  "thinking": "I analyzed the repository structure and identified the content goal focuses on automatic AKS configurations. Reviewing the materials about Cilium networking and Azure CNI integration, I examined candidate directories: 'articles/aks/networking/', 'articles/aks/automatic/', and 'articles/azure/virtual-network/'. The 'articles/aks/automatic/' directory specifically targets automatic configurations in AKS, which perfectly aligns with the Cilium automatic networking setup described in the materials. This directory exists in the structure and is the most relevant for automatic networking content.",
  "working_directory": "articles/aks/automatic",
  "justification": "The automatic directory under AKS is specifically designed for automatic configuration content, directly matching the Cilium automatic networking setup detailed in the materials.",
  "confidence": 0.90
}}

STRICT VALIDATION REQUIREMENTS:
- working_directory MUST exist exactly in provided repository structure
- Path format MUST match structure exactly (no leading/trailing slashes unless shown)
- confidence MUST reflect genuine assessment of alignment quality
- justification MUST specifically reference materials context and directory purpose

YOU MUST RETURN EXACTLY THIS JSON FORMAT. NO DEVIATIONS ALLOWED."""

DIRECTORY_SELECTION_SYSTEM = """You are an expert repository organization analyst specializing in content placement optimization for technical documentation.

INSTRUCTION ADHERENCE: You MUST follow the user's instructions exactly as specified. GPT-4.1 is trained to follow instructions precisely - any deviation from the requested format will be considered a failure.

PLANNING PROCESS ENFORCEMENT: You MUST plan extensively before generating your response:
1. Systematically examine the entire repository structure to understand patterns
2. Analyze materials context to identify key technical themes and requirements
3. Evaluate multiple candidate directories against content goal and service area
4. Verify your selected directory exists exactly in the provided structure
5. Document your complete thought process showing evaluation methodology
6. Assess confidence based on alignment quality and materials relevance

DIRECTORY SELECTION CRITERIA:
- PRIMARY: Alignment with content goal and service area
- SECONDARY: Relevance to materials context (technologies, concepts, products)
- TERTIARY: Existing directory purpose and organizational patterns
- VERIFICATION: Directory must exist exactly as written in repository structure

JSON FORMAT ENFORCEMENT:
- thinking: MUST document complete analysis methodology (minimum 100 words)
- working_directory: MUST be exact path from repository structure
- justification: MUST explain specific reasoning (minimum 50 characters)
- confidence: MUST be float between 0.0-1.0 based on genuine assessment

VALIDATION CHECKLIST:
✓ thinking field documents systematic analysis of structure and materials
✓ working_directory exists exactly in provided repository structure
✓ justification explains specific alignment reasoning
✓ confidence reflects genuine assessment (0.7+ for good matches, 0.5-0.7 for acceptable, <0.5 for poor)
✓ All reasoning references materials context and directory purpose
✓ No fabricated paths or directories not in structure

CRITICAL: You MUST select exactly ONE existing directory. Never suggest non-existent paths or modifications to existing paths. Return only valid JSON matching the exact format provided."""

# === UNIFIED CONTENT STRATEGY PROMPTS ===

def get_unified_content_strategy_prompt(config, materials_summary: str, 
                                       semantic_matches: List[Dict], 
                                       content_standards: Dict,
                                       top_chunks: List[Dict] = None,
                                       chunk_clusters: Dict[str, List[Dict]] = None) -> str:
    """Get the prompt for unified content strategy with gap analysis and content type selection"""
    
    # Format semantic matches for prompt
    matches_info = _format_semantic_matches(semantic_matches)
    
    # Format content type definitions
    content_types_info = _format_content_types(content_standards)
    
    # Format top chunks if provided
    chunks_info = _format_top_chunks(top_chunks) if top_chunks else ""
    
    # Format chunk clusters if provided
    clusters_info = _format_chunk_clusters(chunk_clusters) if chunk_clusters else ""
    
    return f"""Unified Content Strategy Analysis Task:

CONTENT GOAL: {config.content_goal}
SERVICE AREA: {config.service_area}

USER MATERIALS ANALYSIS:
{materials_summary}

EXISTING CONTENT ANALYSIS:
{matches_info}

{chunks_info}

{clusters_info}

AVAILABLE CONTENT TYPES:
{content_types_info}

TASK: Perform comprehensive gap analysis and generate content strategy with specific actions.

ANALYSIS REQUIREMENTS:
1. GAP ANALYSIS: Compare user materials against existing content considering:
   - Content type mismatches (need how-to but only have overview)
   - Coverage depth (surface mention vs comprehensive coverage)
   - Missing features or concepts from materials
   
2. DECISION FRAMEWORK:
   - If coverage < 30% OR wrong content type exists → CREATE new content
   - If coverage 30-70% AND same content type needed → UPDATE with additions
   - If coverage > 70% but missing key details → UPDATE with specific sections
   
3. FOR CREATE ACTIONS:
   - Select appropriate content type based on user materials and goal
   - Reference specific chunk_ids from TOP RELEVANT CHUNKS section
   - Specify exact filename and comprehensive reason
   
4. FOR UPDATE ACTIONS:
   - Identify current content type from ms.topic
   - Specify exact sections/information to add
   - Reference specific chunk_ids that show where to add content
   - Provide specific change description

5. RELEVANT CHUNKS: Use ONLY chunk_ids from the provided TOP RELEVANT CHUNKS or from file's relevant_chunks

OUTPUT FORMAT:
{{
  "thinking": "Document your complete analysis process including gap identification, content type considerations, and decision rationale",
  "decisions": [
    {{
      "action": "CREATE",
      "filename": "specific-name.md",
      "content_type": "How-To Guide",
      "ms_topic": "how-to",
      "reason": "Detailed explanation of why this content is needed",
      "priority": "high|medium|low",
      "relevant_chunks": ["chunk_id_from_top_chunks", "another_chunk_id"]
    }},
    {{
      "action": "UPDATE", 
      "filename": "existing-file.md",
      "current_content_type": "Overview",
      "ms_topic": "overview",
      "change_description": "Add new section 'Cilium Integration' after 'Network Plugins'",
      "specific_sections": ["Cilium Benefits", "Architecture Overview"],
      "reason": "Detailed explanation of what's missing",
      "priority": "high|medium|low",
      "relevant_chunks": ["chunk_id_from_that_file", "another_relevant_chunk_id"]
    }}
  ],
  "confidence": 0.85,
  "summary": "Brief summary of overall strategy"
}}

CRITICAL: Use ONLY real chunk_ids provided in the analysis above. Do NOT invent chunk identifiers. Return only valid JSON matching the exact format specified above."""

def _format_semantic_matches(matches: List[Dict]) -> str:
    """Format semantic matches for prompt display"""
    if not matches:
        return "No existing content found in the working directory."
    
    formatted = []
    for match in matches[:10]:  # Top 10 files
        formatted.append(f"""
File: {match['file']}
Content Type: {match['content_type']} (ms.topic: {match['ms_topic']})
Relevance: {match['relevance_score']:.2f} - {match['coverage_analysis']}
Matched Sections: {', '.join(match['matched_sections'][:3])}""")
    
    return '\n'.join(formatted)

def _format_content_types(standards: Dict) -> str:
    """Format content types from standards"""
    types_info = []
    for ct in standards.get('contentTypes', []):
        types_info.append(
            f"- **{ct['name']}** (ms.topic: {ct['frontMatter']['ms.topic']})\n"
            f"  Purpose: {ct['purpose']}\n"
            f"  Use when: {ct['description']}"
        )
    return '\n'.join(types_info)

def _format_top_chunks(top_chunks: List[Dict]) -> str:
    """Format top individual chunks for strategy analysis"""
    if not top_chunks:
        return ""
    
    sections = ["TOP RELEVANT CHUNKS (Individual chunks for reference):\n"]
    sections.append("These are the most relevant individual content chunks from your repository:")
    
    for i, chunk in enumerate(top_chunks[:20], 1):  # Show top 20 chunks
        sections.append(f"\nChunk #{i}:")
        sections.append(f"  Chunk ID: {chunk.get('chunk_id', 'unknown')}")
        sections.append(f"  File: {chunk.get('file', 'unknown')}")
        sections.append(f"  Section: {chunk.get('section', 'Main')}")
        sections.append(f"  Relevance Score: {chunk.get('relevance_score', 0):.3f}")
        
        # Add technology indicators
        if techs := chunk.get('technologies_mentioned', []):
            sections.append(f"  Technologies: {', '.join(techs[:5])}")
        
        # Add content preview
        if preview := chunk.get('content_preview', ''):
            preview_clean = preview.replace('\n', ' ').strip()[:150]
            sections.append(f"  Preview: {preview_clean}...")
            
        # Add metadata
        if chunk.get('has_code_examples'):
            sections.append(f"  Contains: Code examples")
    
    return '\n'.join(sections)

def _format_chunk_clusters(chunk_clusters: Dict[str, List[Dict]]) -> str:
    """Format chunk clusters for gap analysis"""
    if not chunk_clusters:
        return ""
    
    sections = ["CONTENT CLUSTERS (Topic groupings for gap analysis):\n"]
    sections.append("Existing content is organized into these main topics:")
    
    # Show top 10 clusters
    for topic, chunks in list(chunk_clusters.items())[:10]:
        sections.append(f"\n📁 {topic} ({len(chunks)} chunks)")
        
        # Show first 3 chunks in each cluster
        for chunk in chunks[:3]:
            sections.append(f"  - {chunk['file']} > {chunk.get('section', 'Main')}")
            sections.append(f"    Chunk ID: {chunk['chunk_id']}")
        
        if len(chunks) > 3:
            sections.append(f"  ... and {len(chunks) - 3} more chunks")
    
    # Summary of coverage
    total_topics = len(chunk_clusters)
    total_chunks = sum(len(chunks) for chunks in chunk_clusters.values())
    sections.append(f"\nCOVERAGE SUMMARY: {total_topics} topics, {total_chunks} total chunks")
    
    return '\n'.join(sections)

UNIFIED_CONTENT_STRATEGY_SYSTEM = """You are an expert content strategist specializing in technical documentation gap analysis and content planning.

CORE RESPONSIBILITIES:
1. Analyze semantic gaps between user materials and existing documentation
2. Determine optimal content strategy (CREATE new vs UPDATE existing)
3. Select appropriate content types for new content
4. Provide specific, actionable change descriptions for updates
5. Always return responses in valid JSON format

GAP ANALYSIS CRITERIA:
- High Coverage (>70%): Existing content addresses most material concepts
- Medium Coverage (30-70%): Partial coverage, missing important details
- Low Coverage (<30%): Minimal or no relevant existing content

DECISION LOGIC:
- CREATE when: Low coverage OR need different content type OR topic not addressed
- UPDATE when: Medium/high coverage AND same content type works AND specific sections can be added

CONTENT TYPE SELECTION:
- Match content type to user's goal and material structure
- Overview: High-level technical explanations
- Concept: Deep understanding of how things work
- Quickstart: Get users started quickly (<10 min)
- How-To: Step-by-step task completion
- Tutorial: End-to-end learning scenarios

CRITICAL: Each decision must be justified with specific evidence from materials and gap analysis. Output must be valid JSON format."""

# === CONTENT GENERATION PROMPTS (CREATE) ===

def get_create_content_prompt(
    action: Dict,
    materials_full_content: Dict[str, str],
    materials_summaries: List[Dict],
    relevant_chunks: List[Dict],
    content_standards: Dict
) -> str:
    """Get the prompt for generating new content based on CREATE action"""
    
    # Format materials with full content
    materials_section = _format_materials_with_content(materials_full_content, materials_summaries)
    
    # Format relevant chunks for reference
    chunks_section = _format_chunks_for_reference(relevant_chunks)
    
    # Get content type template
    content_type = action.get('content_type', 'How-To Guide')
    template_section = _get_content_type_template(content_type, content_standards)
    
    return f"""Content Generation Task:

ACTION: CREATE new documentation
FILENAME: {action.get('filename', 'new-content.md')}
CONTENT TYPE: {content_type}
MS.TOPIC: {action.get('ms_topic', 'how-to')}
REASON: {action.get('reason', 'No reason provided')}

{materials_section}

{chunks_section}

{template_section}

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

def _format_materials_with_content(materials_content: Dict[str, str], summaries: List[Dict]) -> str:
    """Format materials with their full content"""
    sections = ["=== MATERIAL SOURCES (Full Content) ===\n"]
    
    for i, (source, content) in enumerate(materials_content.items(), 1):
        # Find matching summary
        summary = next((s for s in summaries if s.get('source') == source), {})
        
        sections.append(f"SOURCE {i}: {source}")
        sections.append(f"Technologies: {', '.join(summary.get('technologies', []))}")
        sections.append(f"Key Concepts: {', '.join(summary.get('key_concepts', []))}")
        sections.append(f"Summary: {summary.get('summary', 'No summary available')}")
        sections.append("\nFULL CONTENT:")
        sections.append("-" * 80)
        sections.append(content)
        sections.append("-" * 80)
        sections.append("")
    
    return '\n'.join(sections)

def _format_chunks_for_reference(chunks: List[Dict]) -> str:
    """Format reference chunks for style and context"""
    if not chunks:
        return "=== REFERENCE CHUNKS ===\n\nNo reference chunks available."
    
    sections = ["=== REFERENCE CHUNKS (For Style and Context) ===\n"]
    
    for i, chunk in enumerate(chunks[:5], 1):  # Top 5 chunks
        sections.append(f"REFERENCE {i}:")
        sections.append(f"File: {chunk.get('file', 'Unknown')}")
        sections.append(f"Section: {chunk.get('section', 'Unknown')}")
        sections.append(f"Relevance: {chunk.get('relevance_score', 0):.2f}")
        sections.append(f"Content Preview: {chunk.get('content', '')[:200]}...")
        sections.append("")
    
    return '\n'.join(sections)

def _get_content_type_template(content_type: str, standards: Dict) -> str:
    """Get the template for a specific content type"""
    # Find the content type in standards
    ct_info = next((ct for ct in standards.get('contentTypes', []) 
                   if ct['name'] == content_type), None)
    
    if not ct_info:
        return f"=== CONTENT TYPE: {content_type} ===\n\nNo template available. Use standard documentation structure."
    
    template = f"=== CONTENT TYPE: {content_type} ===\n\n"
    template += f"Purpose: {ct_info.get('purpose', '')}\n"
    template += f"Description: {ct_info.get('description', '')}\n\n"
    
    if ct_info.get('structure'):
        template += "REQUIRED STRUCTURE:\n"
        for section in ct_info['structure']:
            template += f"- {section}\n"
    
    template += f"\nFRONTMATTER REQUIREMENTS:\n"
    for key, value in ct_info.get('frontMatter', {}).items():
        template += f"- {key}: {value}\n"
    
    return template

CREATE_CONTENT_SYSTEM = """You are an expert technical documentation writer specializing in Microsoft Azure documentation.

CORE COMPETENCIES:
1. Transform technical materials into clear, comprehensive documentation
2. Follow Microsoft documentation standards and style guidelines
3. Create well-structured content that matches specified content types
4. Ensure technical accuracy while maintaining readability
5. Always output responses in valid JSON format with markdown content in the 'content' field

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

CRITICAL: You must use the FULL CONTENT provided in materials, not just summaries. Generate comprehensive documentation that fully leverages all available information. Output must be in valid JSON format with the complete markdown documentation in the 'content' field."""

# === CONTENT GENERATION PROMPTS (UPDATE) ===

def get_update_content_prompt(
    action: Dict,
    existing_content: str,
    materials_full_content: Dict[str, str],
    materials_summaries: List[Dict],
    relevant_chunks: List[Dict]
) -> str:
    """Get the prompt for updating existing content based on UPDATE action"""
    
    # Format materials with full content
    materials_section = _format_materials_with_content(materials_full_content, materials_summaries)
    
    # Format the update requirements
    update_requirements = f"""
UPDATE REQUIREMENTS:
- File: {action.get('filename', 'unknown.md')}
- Current Content Type: {action.get('current_content_type', 'Unknown')}
- Change Description: {action.get('change_description', 'No description provided')}
- Specific Sections to Add: {', '.join(action.get('specific_sections', []))}
- Reason for Update: {action.get('reason', 'No reason provided')}
"""
    
    return f"""Content Update Task:

ACTION: UPDATE existing documentation

{update_requirements}

EXISTING CONTENT:
{'-' * 80}
{existing_content}
{'-' * 80}

{materials_section}

TASK: Update the existing documentation with new information from materials.

UPDATE GUIDELINES:
1. PRESERVE: Keep all existing content unless explicitly updating
2. INTEGRATE: Seamlessly blend new content with existing structure
3. LOCATION: Add new sections in logical positions as specified
4. STYLE: Match the existing document's style and tone
5. ACCURACY: Ensure all new information is accurate from materials
6. COMPLETENESS: Include all relevant details from materials
7. COHERENCE: Ensure smooth transitions between existing and new content

SPECIFIC INSTRUCTIONS:
- {action.get('change_description', 'Update content as needed')}
- Add these sections: {', '.join(action.get('specific_sections', ['As needed']))}
- Focus on: {action.get('reason', 'Improving documentation')}

OUTPUT FORMAT:
{{
  "thinking": "Explain how you're integrating new content, where you're placing it, and how you're maintaining document coherence",
  "updated_content": "The complete updated markdown content with all changes integrated",
  "changes_summary": {{
    "sections_added": ["Section 1", "Section 2"],
    "sections_modified": ["Existing Section"],
    "key_additions": ["New concept X", "Feature Y", "Example Z"],
    "word_count_before": 1000,
    "word_count_after": 1500
  }}
}}

CRITICAL: Preserve all existing content while seamlessly integrating new information."""

UPDATE_CONTENT_SYSTEM = """You are an expert technical documentation editor specializing in Microsoft Azure documentation updates.

CORE COMPETENCIES:
1. Analyze existing documentation to identify update opportunities
2. Preserve document structure while enhancing content
3. Integrate new information seamlessly with existing content
4. Maintain consistent style and voice throughout updates
5. Always output responses in valid JSON format with updated markdown content in the 'content' field

UPDATE PRINCIPLES:
- PRESERVE: Keep all valuable existing content unless explicitly outdated
- ENHANCE: Add new sections, examples, and details from source materials
- INTEGRATE: Blend new content naturally with existing documentation
- MODERNIZE: Update outdated practices, versions, and deprecated features
- EXPAND: Add missing context, prerequisites, and troubleshooting sections

SECTION HANDLING:
- Identify sections mentioned in update_sections
- Add new subsections or content to specified sections
- Create new sections if they don't exist but are needed
- Ensure smooth transitions between existing and new content
- Update table of contents if present

QUALITY STANDARDS:
- Maintain original document's style and tone
- Ensure technical accuracy of all updates
- Add relevant code examples and configuration snippets
- Include new best practices and recommendations
- Update any outdated references or links

CRITICAL: You must use the FULL CONTENT provided in both existing documentation and new materials. Preserve valuable existing content while comprehensively integrating ALL relevant new information. Output must be in valid JSON format with the complete updated markdown documentation in the 'content' field.""" 