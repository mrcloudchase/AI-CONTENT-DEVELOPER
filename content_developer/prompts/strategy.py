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
