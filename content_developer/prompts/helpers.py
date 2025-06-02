"""
Helper functions for prompt formatting
"""
from typing import Dict, List


def format_semantic_matches(matches: List[Dict]) -> str:
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


def format_content_types(standards: Dict) -> str:
    """Format content types from standards"""
    types_info = []
    for ct in standards.get('contentTypes', []):
        types_info.append(
            f"- **{ct['name']}** (ms.topic: {ct['frontMatter']['ms.topic']})\n"
            f"  Purpose: {ct['purpose']}\n"
            f"  Use when: {ct['description']}"
        )
    return '\n'.join(types_info)


def format_top_chunks(top_chunks: List[Dict]) -> str:
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


def format_chunk_clusters(chunk_clusters: Dict[str, List[Dict]]) -> str:
    """Format chunk clusters for gap analysis"""
    if not chunk_clusters:
        return ""
    
    sections = ["CONTENT CLUSTERS (Topic groupings for gap analysis):\n"]
    sections.append("Existing content is organized into these main topics:")
    
    # Format top clusters
    cluster_sections = _format_top_clusters(chunk_clusters, max_clusters=10)
    sections.extend(cluster_sections)
    
    # Add coverage summary
    summary = _generate_coverage_summary(chunk_clusters)
    sections.append(summary)
    
    return '\n'.join(sections)


def _format_top_clusters(chunk_clusters: Dict[str, List[Dict]], max_clusters: int = 10) -> List[str]:
    """Format the top N clusters with their chunks"""
    sections = []
    
    for topic, chunks in list(chunk_clusters.items())[:max_clusters]:
        sections.append(f"\n📁 {topic} ({len(chunks)} chunks)")
        
        # Format chunks in cluster
        chunk_sections = _format_cluster_chunks(chunks, max_chunks=3)
        sections.extend(chunk_sections)
        
        # Add overflow indicator
        if len(chunks) > 3:
            sections.append(f"  ... and {len(chunks) - 3} more chunks")
    
    return sections


def _format_cluster_chunks(chunks: List[Dict], max_chunks: int = 3) -> List[str]:
    """Format individual chunks within a cluster"""
    sections = []
    
    for chunk in chunks[:max_chunks]:
        sections.append(f"  - {chunk['file']} > {chunk.get('section', 'Main')}")
        sections.append(f"    Chunk ID: {chunk['chunk_id']}")
    
    return sections


def _generate_coverage_summary(chunk_clusters: Dict[str, List[Dict]]) -> str:
    """Generate coverage summary statistics"""
    total_topics = len(chunk_clusters)
    total_chunks = sum(len(chunks) for chunks in chunk_clusters.values())
    return f"\nCOVERAGE SUMMARY: {total_topics} topics, {total_chunks} total chunks"


def format_materials_with_content(materials_content: Dict[str, str], summaries: List[Dict]) -> str:
    """Format materials with their full content"""
    sections = ["=== MATERIAL SOURCES (Full Content) ===\n"]
    
    for i, (source, content) in enumerate(materials_content.items(), 1):
        material_section = _format_single_material(i, source, content, summaries)
        sections.extend(material_section)
    
    return '\n'.join(sections)


def _format_single_material(index: int, source: str, content: str, summaries: List[Dict]) -> List[str]:
    """Format a single material with its metadata and content"""
    sections = []
    
    # Find matching summary
    summary = _find_material_summary(source, summaries)
    
    # Add material header
    sections.append(f"SOURCE {index}: {source}")
    
    # Add metadata
    metadata_sections = _format_material_metadata(summary)
    sections.extend(metadata_sections)
    
    # Add content
    content_sections = _format_material_content(content)
    sections.extend(content_sections)
    
    sections.append("")  # Empty line separator
    
    return sections


def _find_material_summary(source: str, summaries: List[Dict]) -> Dict:
    """Find the summary for a given material source"""
    return next((s for s in summaries if s.get('source') == source), {})


def _format_material_metadata(summary: Dict) -> List[str]:
    """Format material metadata from summary"""
    sections = []
    
    if technologies := summary.get('technologies', []):
        sections.append(f"Technologies: {', '.join(technologies)}")
    
    if key_concepts := summary.get('key_concepts', []):
        sections.append(f"Key Concepts: {', '.join(key_concepts)}")
    
    sections.append(f"Summary: {summary.get('summary', 'No summary available')}")
    
    return sections


def _format_material_content(content: str) -> List[str]:
    """Format the actual content of a material"""
    return [
        "\nFULL CONTENT:",
        "-" * 80,
        content,
        "-" * 80
    ]


def format_chunks_for_reference(chunks: List[Dict]) -> str:
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


def get_content_type_template(content_type: str, standards: Dict) -> str:
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


def format_microsoft_elements(content_standards: Dict) -> str:
    """Format Microsoft-specific formatting elements for prompt inclusion"""
    if not content_standards:
        return ""
    
    formatting_elements = content_standards.get('formattingElements', [])
    code_guidelines = content_standards.get('codeGuidelines', {})
    
    # Build formatting guide
    lines = ["=== MICROSOFT DOCUMENTATION FORMATTING ===\n"]
    
    # Add special elements
    lines.append("SPECIAL FORMATTING ELEMENTS:")
    for element in formatting_elements:
        lines.append(f"\n{element['name']}:")
        lines.append(f"Format: {element['format']}")
        if element['name'] in ['Note', 'Warning', 'Tip']:
            lines.append(f"Use for: {element['name'].lower()} callouts that need reader attention")
        elif element['name'] == 'Checklist':
            lines.append("Use for: Tutorial objectives or feature lists")
        elif element['name'] == 'Next step link':
            lines.append("Use for: Prominent navigation to the next article in a series")
    
    # Add code language guidelines
    lines.append("\n\nCODE BLOCK LANGUAGES:")
    languages = code_guidelines.get('languages', [])
    for lang in languages:
        lines.append(f"- {lang['syntax']} - {lang['useFor']}")
    
    # Add common tab groups
    tab_groups = content_standards.get('commonTabGroups', [])
    if tab_groups:
        lines.append("\n\nTAB GROUPS (for multiple approaches):")
        lines.append("Format: #### [Tab Name](#tab/tab-id)")
        lines.append("Common groups: Azure portal, Azure CLI, PowerShell, ARM template, Bicep")
        lines.append("End with: ---")
    
    # Add security reminders
    lines.append("\n\nSECURITY REQUIREMENTS:")
    lines.append("- Use <placeholder-name> for all sensitive values")
    lines.append("- NEVER include real credentials or secrets")
    lines.append("- Show managed identity approaches when applicable")
    
    return "\n".join(lines) 