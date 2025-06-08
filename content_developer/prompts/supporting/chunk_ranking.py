"""
Chunk Ranking Prompt - Supporting Prompts
Ranks document chunks by relevance to a query
"""
from typing import List, Dict


def get_chunk_ranking_prompt(query: str, chunks: List[Dict]) -> str:
    """Get the prompt for ranking document chunks by relevance"""
    
    # Format chunks for display
    chunks_display = []
    for i, chunk in enumerate(chunks):
        chunks_display.append(f"""
Chunk {i+1}:
- File: {chunk.get('file_path', 'Unknown')}
- Section: {' > '.join(chunk.get('heading_path', []))}
- Content: {chunk.get('content', '')[:500]}...
""")
    
    return f"""Rank the following documentation chunks by their relevance to the query.

QUERY: {query}

CHUNKS TO RANK:
{chr(10).join(chunks_display)}

Ranking criteria:
1. Direct relevance to the query topic
2. Completeness of information
3. Technical depth appropriateness
4. Context and clarity
5. Practical applicability

For each chunk, assess:
- How well it addresses the query
- What specific value it provides
- Whether it's essential, helpful, or marginally related

REQUIRED OUTPUT:
Return a JSON object with these exact fields:

{{
  "thinking": [
    "YOUR understanding of the query intent",
    "YOUR assessment of each chunk's relevance",
    "YOUR ranking rationale"
  ],
  "rankings": [
    {{
      "chunk_id": "1",
      "relevance_score": 9.5,
      "relevance_reason": "Directly addresses the query with comprehensive information about the topic"
    }},
    {{
      "chunk_id": "2",
      "relevance_score": 7.0,
      "relevance_reason": "Provides useful context and related examples"
    }}
  ],
  "top_chunks": ["1", "3", "5"],
  "key_themes": ["authentication", "security best practices", "OAuth implementation"]
}}

FIELD REQUIREMENTS:
- thinking: Array of YOUR ACTUAL analysis steps (2-10 items)
- rankings: Array of chunk rankings, each containing:
  - chunk_id: String identifier of the chunk (1, 2, 3, etc.)
  - relevance_score: Number between 0-10 (10 = most relevant)
  - relevance_reason: Explanation of the relevance score
- top_chunks: Array of chunk IDs for the most relevant chunks
- key_themes: Array of main themes found across relevant chunks"""


CHUNK_RANKING_SYSTEM = """You are an expert at analyzing and ranking technical documentation content for relevance.

CORE COMPETENCIES:
1. Understanding query intent and information needs
2. Assessing content relevance and quality
3. Recognizing technical depth and completeness
4. Evaluating practical applicability
5. Determining information priority

RANKING PRINCIPLES:
1. DIRECT RELEVANCE: Content that directly addresses the query
2. COMPLETENESS: Comprehensive coverage of the topic
3. CLARITY: Well-explained, easy to understand content
4. PRACTICAL VALUE: Actionable information and examples
5. CONTEXT: Necessary background or supporting information

RELEVANCE ASSESSMENT:
- Essential: Directly answers the query, must-read content
- Highly Relevant: Strong connection, valuable supporting information
- Relevant: Related content that provides useful context
- Marginally Relevant: Tangential connection, optional reading
- Not Relevant: No meaningful connection to the query

RANKING FACTORS:
1. Topic match - How closely the content matches the query
2. Information density - Amount of relevant information
3. Quality - Clarity, accuracy, and completeness
4. Uniqueness - Information not found in other chunks
5. User value - Practical benefit to someone seeking this information

ANALYSIS APPROACH:
- Understand the query's core information need
- Evaluate each chunk against that need
- Consider the chunk's role in the broader context
- Assess unique value proposition
- Rank based on overall relevance score

OUTPUT REQUIREMENTS:
- Clear ranking with numerical scores
- Specific justification for each ranking
- Identification of most valuable content
- Honest assessment of relevance
- Actionable insights for content usage.""" 