# Content Strategy Planning for Phase 2

## Overview

Phase 2 focuses on **strategic content decision-making** rather than blind content creation. The goal is to determine whether to CREATE new content, UPDATE existing content, or use hybrid approaches based on semantic analysis of existing content vs. user goals and materials.

## Core Philosophy

> **Content Strategy Engine**: Analyze existing content landscape to make intelligent decisions about content lifecycle actions, mimicking how experienced content strategists think.

## Technical Architecture

### 1. Embeddings-Based Content Discovery

#### Hierarchical Section-Based Chunking Strategy
```python
@dataclass
class DocumentChunk:
    content: str
    file_path: str
    chunk_type: str  # "frontmatter", "section", "combined"
    heading_path: List[str]  # ["Getting Started", "Installation", "Prerequisites"]
    section_level: int       # 1 for #, 2 for ##, etc.
    chunk_index: int         # Position within document
    
    # Frontmatter metadata propagated to ALL chunks from same file
    frontmatter: Dict[str, Any]  # ms.service, ms.topic, title, description, etc.
    
    # Enhanced content for embedding (includes frontmatter context)
    embedding_content: str
    embedding: Optional[np.array] = None
```

#### Chunking Rules
- **Primary Strategy**: Section-based chunking respecting markdown hierarchy
- **Size Management**: Max 1500 chars per chunk, combine small sections, split large ones at logical boundaries
- **Frontmatter Integration**: Enhance embedding content with metadata context
- **Structure Preservation**: Maintain heading paths for context

#### Example Chunking Output
```
File: "container-networking.md"
├── Chunk 1: "# Container Networking" + intro (800 chars)
├── Chunk 2: "## Azure CNI Overview" + content (1200 chars)  
├── Chunk 3: "### Installation Steps" + content (1400 chars)
└── Chunk 4: "### Troubleshooting" + content (900 chars)
```

### 2. Semantic Decision Pipeline

#### Phase 2 Processing Flow
```
Phase 1 Result → Content Discovery → Embeddings Generation → Similarity Matching → Strategic LLM Decision → User Confirmation → Action Plan
```

#### Intent Embedding Creation
```python
def create_user_intent_embedding(content_goal: str, service_area: str, materials: List[Dict]) -> np.array:
    intent_text = f"""
    Content Goal: {content_goal}
    Service Area: {service_area}
    Key Technologies: {extract_technologies(materials)}
    Key Concepts: {extract_concepts(materials)}
    Summary: {create_materials_summary(materials)}
    """
    return get_embedding(intent_text)
```

#### Similarity-Based Content Discovery
- Calculate cosine similarity between user intent and all existing chunks
- Return top 5-10 most semantically similar content pieces
- Focus LLM analysis only on relevant existing content

### 3. CREATE vs UPDATE Decision Engine

#### Strategic LLM Analysis
```python
class CreateUpdateDecisionProcessor(BaseProcessor):
    def process(self, user_intent: Dict, candidate_chunks: List[DocumentChunk]) -> Dict:
        prompt = f"""
        Content Goal: {user_intent['goal']}
        Service Area: {user_intent['service_area']}
        
        User Materials Summary:
        {user_intent['materials_summary']}
        
        Most Similar Existing Content:
        {existing_content_summary}
        
        Decision Instructions:
        1. Analyze semantic overlap between user materials and existing content
        2. Evaluate if existing content can be enhanced to meet the goal
        3. Consider content structure and scope compatibility
        4. Decide: UPDATE existing content OR CREATE new content
        
        Return JSON: {{
            "thinking": "step-by-step analysis",
            "decision": "CREATE|UPDATE", 
            "target_files": ["file1.md", "file2.md"],
            "reasoning": "detailed justification",
            "confidence": 0.85
        }}
        """
```

#### Decision Criteria

**UPDATE Decision Factors:**
- Semantic overlap >75% with existing content
- Structural compatibility with existing document
- Existing content provides solid foundation to build upon
- Enhancement would improve rather than fragment content

**CREATE Decision Factors:**
- Semantic gap in existing content landscape
- New technologies/approaches not covered
- Scope incompatibility with existing structure
- Would create unfocused "frankenstein" documents if merged

#### Example Decision Scenarios

**UPDATE Scenario:**
```
User Goal: "Add Cilium CNI setup instructions"
Top Similar: "azure-cni-overview.md" (similarity: 0.78)
LLM Analysis: "Existing CNI documentation covers networking concepts well. 
               Adding Cilium-specific section would enhance existing structure."
Decision: UPDATE azure-cni-overview.md
```

**CREATE Scenario:**
```
User Goal: "Kubernetes troubleshooting with GPU workloads" 
Top Similar: "general-troubleshooting.md" (similarity: 0.65)
LLM Analysis: "Existing troubleshooting is generic. GPU-specific issues require
               specialized content with different diagnostic approaches."
Decision: CREATE gpu-troubleshooting-guide.md
```

## Implementation Efficiency

### Massive LLM Call Reduction
- **Before**: 50+ LLM calls (summarize every file)
- **After**: 6-11 LLM calls (5-10 similarity-selected summaries + 1 strategy decision)
- **Cost Reduction**: ~80-90%
- **Quality Improvement**: Focus on relevant content only

### Technical Dependencies
- **Embedding Model**: OpenAI `text-embedding-3-small` (good cost/performance)
- **Cache Strategy**: Store embeddings with file modification timestamps
- **Batch Processing**: Generate embeddings for multiple chunks in single API call

## Architecture Integration with Phase 1

### Reused Patterns from Phase 1
- **Modular processor architecture** with BaseProcessor inheritance
- **Rich LLM prompting** with explicit planning and thinking fields
- **Interactive confirmation UX** similar to directory selection
- **Comprehensive logging** and audit trails
- **Auto-confirm mode** for CI/CD pipelines
- **Graceful fallbacks** when AI encounters issues

### Data Flow from Phase 1
```python
# Phase 1 Output becomes Phase 2 Input
phase1_result = Result(
    working_directory="articles/azure-arc/kubernetes",
    material_summaries=[...],  # Rich summaries with thinking
    content_goal="add document to automatic",
    service_area="aks"
)

# Phase 2 uses this context for content strategy
phase2_input = ContentStrategyInput(
    working_directory_path=phase1_result.working_directory_full_path,
    materials=phase1_result.material_summaries,
    content_goal=phase1_result.content_goal,
    service_area=phase1_result.service_area
)
```

## Key Benefits

### Strategic Intelligence
- **Content lifecycle awareness**: Understands when to enhance vs. create new
- **Semantic understanding**: Decisions based on content meaning, not dates
- **Resource efficiency**: Focuses effort where it adds most value
- **Quality consistency**: Builds on existing content patterns and styles

### User Experience
- **Transparent reasoning**: Shows why CREATE vs UPDATE decisions were made
- **Interactive confirmation**: User can override AI recommendations
- **Granular control**: Can see which specific files/sections are involved
- **Audit trail**: Full logging of decision-making process

## Future Considerations

### Potential Extensions
- **ARCHIVE decisions**: Identify deprecated/redundant content for removal
- **PRESERVE tags**: Mark content that needs no changes
- **Priority scoring**: Order recommended actions by impact/effort
- **Dependency mapping**: Understand content relationships and TOC impacts

### Integration Points
- **Phase 3**: Content generation based on Phase 2 strategy decisions
- **CI/CD workflows**: Automated content strategy analysis
- **Content governance**: Regular content health assessments
- **Team workflows**: Content planning and review processes

---

*This document captures the strategic design for Phase 2 content decision-making engine, focusing on intelligent CREATE vs UPDATE determinations using embeddings-based semantic analysis.* 