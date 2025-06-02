"""
Content strategy prompts for AI Content Developer
"""
from typing import Dict, List

from .helpers import (
    format_semantic_matches, format_content_types,
    format_top_chunks, format_chunk_clusters
)


def get_unified_content_strategy_prompt(config, materials_summary: str, 
semantic_matches: List[Dict], 
content_standards: Dict,
top_chunks: List[Dict] = None,
chunk_clusters: Dict[str, List[Dict]] = None) -> str:
    """Get the prompt for unified content strategy with gap analysis and content type selection"""
    
    # Format semantic matches for prompt
    matches_info = format_semantic_matches(semantic_matches)
    
    # Format content type definitions
    content_types_info = format_content_types(content_standards)
    
    # Format top chunks if provided
    chunks_info = format_top_chunks(top_chunks) if top_chunks else ""
    
    # Format chunk clusters if provided
    clusters_info = format_chunk_clusters(chunk_clusters) if chunk_clusters else ""
    
    return f"""Unified Content Strategy Analysis Task:

CONTENT GOAL: {config.content_goal}
SERVICE AREA: {config.service_area}
TARGET AUDIENCE: {config.audience}
AUDIENCE LEVEL: {config.audience_level}

USER MATERIALS ANALYSIS:
{materials_summary}

EXISTING CONTENT ANALYSIS:
{matches_info}

{chunks_info}

{clusters_info}

AVAILABLE CONTENT TYPES:
{content_types_info}

TASK: Perform comprehensive gap analysis and generate content strategy with specific actions.

AUDIENCE CONSIDERATIONS:
- Target readers: {config.audience}
- Technical depth: {config.audience_level} level
- Beginner: Include prerequisites, detailed explanations, basic concepts
- Intermediate: Balance explanation with technical detail
- Advanced: Focus on implementation, optimization, and edge cases

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
   - Create detailed content_brief with:
     * Clear objective stating what reader will accomplish
     * Specific topics from materials that must be covered
     * Prerequisites based on existing content analysis
     * Related docs from the repository to reference
     * Logical next steps based on content progression
     * Technical depth guidance based on audience level
     * Specific examples from materials to include
   
4. FOR UPDATE ACTIONS:
   - Identify current content type from ms.topic
   - Specify exact sections/information to add
   - Reference specific chunk_ids that show where to add content
   - Provide specific change description
   - Create detailed content_brief with:
     * Update objective explaining the gap being filled
     * Specific sections to add with placement guidance
     * Sections to modify with clear preservation instructions
     * New examples from materials to incorporate
     * Additional links to connect updated content
     * Style consistency requirements

5. RELEVANT CHUNKS: Use ONLY chunk_ids from the provided TOP RELEVANT CHUNKS or from file's relevant_chunks

OUTPUT FORMAT:
{{
  "thinking": "1. Gap analysis: Document your complete analysis process including gap identification.\n2. Content type evaluation: Explain content type considerations and selection rationale.\n3. Decision framework: Apply the decision criteria to determine CREATE vs UPDATE actions.\n4. Content brief development: Detail how you developed the specific content briefs.\n5. Final validation: Confirm all decisions align with user goals and existing content patterns.",
  "decisions": [
    {{
      "action": "CREATE",
      "filename": "specific-name.md",
      "content_type": "How-To Guide",
      "ms_topic": "how-to",
      "reason": "Detailed explanation of why this content is needed",
      "priority": "high|medium|low",
      "relevant_chunks": ["chunk_id_from_top_chunks", "another_chunk_id"],
      "content_brief": {{
        "objective": "Clear statement of what the reader will achieve",
        "key_points_to_cover": [
          "Main topic or feature to explain",
          "Important configuration or setup steps",
          "Best practices or optimization tips"
        ],
        "prerequisites_to_state": [
          "Required knowledge or setup",
          "Tools or access needed"
        ],
        "related_docs_to_reference": [
          "Path to prerequisite content",
          "Path to related topics"
        ],
        "next_steps_to_suggest": [
          "What reader might do next",
          "Advanced topics to explore"
        ],
        "technical_depth": "Specific guidance on how deep to go technically",
        "code_examples_needed": [
          "Example commands or configurations",
          "Sample outputs to show"
        ],
        "important_warnings": [
          "Security considerations",
          "Common pitfalls to highlight"
        ]
      }}
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
      "relevant_chunks": ["chunk_id_from_that_file", "another_relevant_chunk_id"],
      "content_brief": {{
        "update_objective": "What gap this update fills",
        "sections_to_add": [
          {{
            "section_name": "Section Title",
            "content_focus": "What this section should cover",
            "placement": "Where in document (after X section)"
          }}
        ],
        "sections_to_modify": [
          {{
            "section_name": "Existing Section",
            "modifications": "What to add or change",
            "preserve": "What to keep unchanged"
          }}
        ],
        "new_examples_to_add": [
          "Specific code or configuration examples"
        ],
        "links_to_add": [
          "New related content to reference"
        ],
        "maintain_style": "Keep consistent with existing document tone and depth"
      }}
    }}
  ],
  "confidence": 0.85,
  "summary": "Brief summary of overall strategy"
}}

CRITICAL: Use ONLY real chunk_ids provided in the analysis above. Do NOT invent chunk identifiers. Return only valid JSON matching the exact format specified above."""


UNIFIED_CONTENT_STRATEGY_SYSTEM = """You are an expert content strategist specializing in technical documentation gap analysis and content planning.

CORE RESPONSIBILITIES:
1. Analyze semantic gaps between user materials and existing documentation
2. Determine optimal content strategy (CREATE new vs UPDATE existing)
3. Select appropriate content types for new content
4. Create detailed content briefs with specific, actionable instructions
5. Provide clear guidance that content writers can follow
6. Always return responses in valid JSON format

YOUR ROLE AS CONTENT STRATEGIST:
- You analyze and plan; you don't write the content
- You create detailed briefs that tell writers exactly what to produce
- You identify relationships between content pieces
- You ensure consistency across the documentation set
- You think about the reader's journey through the docs

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

CONTENT BRIEF REQUIREMENTS:
- Be specific: Don't say "explain networking" - say "explain how Cilium uses eBPF for packet filtering"
- Reference materials: Point to specific concepts from materials that must be included
- Consider flow: Think about what reader knows before and needs after
- Identify examples: Call out specific code/configs from materials to include
- Set boundaries: Be clear about what NOT to cover to maintain focus

CRITICAL: Each decision must be justified with specific evidence from materials and gap analysis. Your content briefs must be detailed enough that a writer can execute without guessing. Output must be valid JSON format."""
