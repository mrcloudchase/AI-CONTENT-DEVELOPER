"""
Helper methods for ContentStrategyProcessor
"""
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import logging

from ..models import DocumentChunk
from ..utils import load_json, read

logger = logging.getLogger(__name__)


class StrategyHelpersMixin:
    """Mixin class providing helper methods for strategy processing"""
    
    def _load_content_standards(self) -> Dict:
        """Load content standards from JSON file"""
        standards_path = Path("content_standards.json")
        if standards_path.exists():
            return load_json(standards_path)
        else:
            logger.warning("content_standards.json not found, using defaults")
            return {
                "contentTypes": [
                    {"name": "Overview", "frontMatter": {"ms.topic": "overview"}, "purpose": "Technical explanation", "description": "Service overview"},
                    {"name": "Concept", "frontMatter": {"ms.topic": "concept-article"}, "purpose": "In-depth explanation", "description": "Conceptual content"},
                    {"name": "Quickstart", "frontMatter": {"ms.topic": "quickstart"}, "purpose": "Quick setup", "description": "Get started quickly"},
                    {"name": "How-To Guide", "frontMatter": {"ms.topic": "how-to"}, "purpose": "Task completion", "description": "Step-by-step guide"},
                    {"name": "Tutorial", "frontMatter": {"ms.topic": "tutorial"}, "purpose": "Learning scenario", "description": "Hands-on tutorial"}
                ]
            }
    
    def _extract_ms_topic(self, file_path: str, chunks: List[DocumentChunk]) -> Optional[str]:
        """Extract ms.topic from existing markdown file"""
        # First try to find from chunks with this file path
        for chunk in chunks:
            if chunk.file_path == file_path and chunk.frontmatter:
                if ms_topic := chunk.frontmatter.get('ms.topic'):
                    return ms_topic
        
        # If not found in chunks, try to read file directly
        try:
            full_path = Path(file_path)
            if full_path.exists():
                content = read(full_path, limit=2000)  # Only need frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        return frontmatter.get('ms.topic')
        except Exception as e:
            logger.warning(f"Could not extract ms.topic from {file_path}: {e}")
        
        return None
    
    def _prepare_semantic_matches(self, similar_chunks: List[DocumentChunk]) -> List[Dict]:
        """Prepare semantic matches in the format expected by the unified prompt"""
        # Group chunks by file with their similarity scores
        chunks_by_file = self._group_chunks_by_file(similar_chunks[:50])
        
        # Create file-level semantic matches
        semantic_matches = []
        for file_path, file_chunks_with_scores in chunks_by_file.items():
            file_match = self._create_file_match(file_path, file_chunks_with_scores)
            semantic_matches.append(file_match)
        
        # Sort by relevance score and return top 10
        semantic_matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        return semantic_matches[:10]
    
    def _group_chunks_by_file(self, chunks: List[DocumentChunk]) -> Dict:
        """Group chunks by file with simulated similarity scores"""
        chunks_by_file = defaultdict(list)
        
        for idx, chunk in enumerate(chunks):
            # Simulate scores based on position (first chunk = highest score)
            score = 0.9 - (idx * 0.01)
            chunks_by_file[chunk.file_path].append((chunk, score))
        
        return chunks_by_file
    
    def _create_file_match(self, file_path: str, file_chunks_with_scores: List[tuple]) -> Dict:
        """Create a file-level semantic match entry"""
        # Extract chunks and scores
        file_chunks = [chunk for chunk, _ in file_chunks_with_scores]
        scores = [score for _, score in file_chunks_with_scores]
        
        # Extract file metadata
        ms_topic, content_type = self._extract_file_metadata(file_chunks)
        
        # Calculate relevance
        relevance_score = sum(scores) / len(scores) if scores else 0.0
        coverage_analysis = self._determine_coverage_level(relevance_score)
        
        # Extract matched sections
        matched_sections = self._extract_matched_sections(file_chunks)
        
        # Prepare chunk details
        file_chunk_details = self._prepare_chunk_details(file_chunks_with_scores[:10])
        
        return {
            'file': Path(file_path).name,
            'content_type': content_type,
            'ms_topic': ms_topic,
            'relevance_score': relevance_score,
            'coverage_analysis': coverage_analysis,
            'matched_sections': matched_sections,
            'relevant_chunks': file_chunk_details
        }
    
    def _extract_file_metadata(self, file_chunks: List[DocumentChunk]) -> tuple:
        """Extract ms.topic and content type from file chunks"""
        ms_topic = 'unknown'
        content_type = 'Unknown'
        
        if not file_chunks or not file_chunks[0].frontmatter:
            return ms_topic, content_type
            
        ms_topic = file_chunks[0].frontmatter.get('ms.topic', 'unknown')
        content_type = self._map_ms_topic_to_content_type(ms_topic)
        
        return ms_topic, content_type
    
    def _determine_coverage_level(self, relevance_score: float) -> str:
        """Determine coverage level based on relevance score"""
        if relevance_score > 0.7:
            return "High coverage - existing content addresses most concepts"
        if relevance_score > 0.4:
            return "Medium coverage - partial coverage, missing important details"
        return "Low coverage - minimal relevant content"
    
    def _extract_matched_sections(self, file_chunks: List[DocumentChunk]) -> List[str]:
        """Extract matched section names from chunks"""
        matched_sections = []
        
        for chunk in file_chunks[:5]:
            if chunk.heading_path:
                matched_sections.append(' > '.join(chunk.heading_path))
        
        return matched_sections
    
    def _prepare_chunk_details(self, chunks_with_scores: List[tuple]) -> List[Dict]:
        """Prepare detailed chunk information for file"""
        chunk_details = []
        
        for chunk, score in chunks_with_scores:
            chunk_details.append({
                'chunk_id': chunk.chunk_id,
                'section': ' > '.join(chunk.heading_path) if chunk.heading_path else 'Main',
                'relevance_score': score,
                'content_preview': chunk.content[:200] if chunk.content else ""
            })
        
        return chunk_details
    
    def _map_ms_topic_to_content_type(self, ms_topic: str) -> str:
        """Map ms.topic value to content type name"""
        mapping = {
            'overview': 'Overview',
            'concept-article': 'Concept',
            'quickstart': 'Quickstart',
            'how-to': 'How-To Guide',
            'tutorial': 'Tutorial'
        }
        return mapping.get(ms_topic, 'Unknown')
    
    def _prepare_top_chunks(self, chunks: List[DocumentChunk]) -> List[Dict]:
        """Prepare individual chunks with full context for strategy generation"""
        top_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'chunk_id': chunk.chunk_id,
                'file': Path(chunk.file_path).name,
                'full_path': chunk.file_path,
                'section': ' > '.join(chunk.heading_path) if chunk.heading_path else 'Main',
                'content_preview': chunk.content[:300] if chunk.content else "",
                'relevance_score': 0.9 - (i * 0.02),  # Score based on position
                'ms_topic': chunk.frontmatter.get('ms.topic', 'unknown') if chunk.frontmatter else 'unknown',
                'heading_level': chunk.section_level,
                'has_code_examples': '```' in (chunk.content or ''),
                'technologies_mentioned': self._extract_technologies_from_chunk(chunk)
            }
            top_chunks.append(chunk_data)
        return top_chunks
    
    def _cluster_chunks_by_topic(self, chunks: List[DocumentChunk]) -> Dict[str, List[Dict]]:
        """Group chunks by semantic topic for gap analysis"""
        clusters = defaultdict(list)
        
        for chunk in chunks:
            # Cluster by main topic (first heading or file name)
            if chunk.heading_path and len(chunk.heading_path) > 0:
                topic = chunk.heading_path[0]
            else:
                topic = Path(chunk.file_path).stem.replace('-', ' ').title()
            
            cluster_entry = {
                'chunk_id': chunk.chunk_id,
                'file': Path(chunk.file_path).name,
                'section': ' > '.join(chunk.heading_path) if chunk.heading_path else 'Main'
            }
            clusters[topic].append(cluster_entry)
        
        # Convert to regular dict and sort by number of chunks
        sorted_clusters = dict(sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True))
        return sorted_clusters
    
    def _extract_technologies_from_chunk(self, chunk: DocumentChunk) -> List[str]:
        """Extract technology mentions from chunk content"""
        technologies = []
        tech_keywords = ['Azure', 'Cilium', 'Kubernetes', 'CNI', 'eBPF', 'Network Policy', 
                        'Pod', 'Container', 'Cluster', 'Node', 'Service Mesh']
        
        content = (chunk.content or '') + ' ' + (chunk.embedding_content or '')
        for tech in tech_keywords:
            if tech.lower() in content.lower():
                technologies.append(tech)
        
        return technologies 