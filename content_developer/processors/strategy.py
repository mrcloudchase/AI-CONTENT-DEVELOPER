"""
Content strategy processor for analyzing gaps and generating content strategy
"""
from collections import defaultdict, namedtuple
from pathlib import Path
from typing import Dict, List, Optional
import logging
import yaml
from datetime import datetime

from ..cache import UnifiedCache
from ..models import Config, ContentStrategy, DocumentChunk
from ..utils import get_hash
from ..prompts import (
    get_unified_content_strategy_prompt,
    UNIFIED_CONTENT_STRATEGY_SYSTEM
)
from .smart_processor import SmartProcessor
from .strategy_debug import StrategyDebugMixin
from .strategy_helpers import StrategyHelpersMixin

logger = logging.getLogger(__name__)


class ContentStrategyProcessor(SmartProcessor, StrategyDebugMixin, StrategyHelpersMixin):
    """Process chunks and materials to generate content strategy"""
    
    def _process(self, chunks: List[DocumentChunk], materials: List[Dict], config: Config, 
                 repo_name: str, working_directory: str) -> ContentStrategy:
        """Process content strategy generation"""
        cache_dir = Path(f"./llm_outputs/embeddings/{repo_name}/{working_directory}")
        intent_embedding = self._create_intent_embedding(config, materials, cache_dir)
        similar_chunks = self._find_similar_content(intent_embedding, chunks, cache_dir)[:10]
        strategy = self._generate_strategy(config, materials, similar_chunks)
        
        # Content types are now handled within the unified prompt
        return strategy
    
    def _create_intent_embedding(self, config: Config, materials: List[Dict], cache_dir: Path) -> List[float]:
        """Create embedding for search intent based on goal and materials"""
        # Build intent text
        intent_text = self._build_intent_text(config, materials)
        
        # Log intent if debugging
        if config.debug_similarity:
            self._log_intent_debug_info(intent_text, materials)
        
        # Try to get from cache
        cache = UnifiedCache(cache_dir)
        cache_key = get_hash(intent_text)
        
        cached_embedding = self._get_cached_embedding(cache, cache_key)
        if cached_embedding:
            return cached_embedding
        
        # Generate new embedding
        return self._generate_intent_embedding(intent_text, cache, cache_key)
    
    def _build_intent_text(self, config: Config, materials: List[Dict]) -> str:
        """Build intent text from config and materials"""
        intent_parts = [f"Goal: {config.content_goal}", f"Service: {config.service_area}"]
        
        # Add material components
        material_components = self._extract_material_components(materials)
        intent_parts.extend(material_components)
        
        return " | ".join(intent_parts)
    
    def _extract_material_components(self, materials: List[Dict]) -> List[str]:
        """Extract components from materials for intent text"""
        components = []
        component_mappings = [
            ('main_topic', 'Topics'),
            ('technologies', 'Technologies'),
            ('key_concepts', 'Key concepts'),
            ('document_type', 'Content types')
        ]
        
        for key, label in component_mappings:
            values = self._extract_values_for_key(materials, key)
            if values:
                components.append(f"{label}: {', '.join(values[:10])}")
        
        return components
    
    def _extract_values_for_key(self, materials: List[Dict], key: str) -> List[str]:
        """Extract values for a specific key from materials"""
        if key in ['technologies', 'key_concepts']:
            # These are lists, need to flatten
            return [value for material in materials for value in material.get(key, [])]
        
        # Single values
        return [material.get(key) for material in materials if material.get(key)]
    
    def _log_intent_debug_info(self, intent_text: str, materials: List[Dict]):
        """Log debug information about intent embedding"""
        self._print_debug_header("INTENT EMBEDDING CONSTRUCTION")
        print(f"\nFull Intent Text ({len(intent_text)} chars):")
        print("-" * 60)
        print(intent_text)
        print("-" * 60)
        print(f"\nExtracted Components:")
        print(f"- Topics: {len([material.get('main_topic', '') for material in materials if material.get('main_topic')])}")
        print(f"- Technologies: {len([value for material in materials for value in material.get('technologies', [])])}")
        print(f"- Concepts: {len([value for material in materials for value in material.get('key_concepts', [])])}")
        print(f"- Document Types: {len(set(material.get('document_type', '') for material in materials if material.get('document_type')))}")
    
    def _get_cached_embedding(self, cache: UnifiedCache, cache_key: str) -> Optional[List[float]]:
        """Try to get embedding from cache"""
        cached = cache.get(cache_key)
        if not cached or 'data' not in cached:
            return None
        
        data = cached['data']
        
        # Handle unified structure
        if isinstance(data, dict) and 'embedding' in data:
            logger.info("Using cached intent embedding")
            embedding = data['embedding']
            # Ensure it's a list of floats
            if embedding:
                return self._ensure_float_list(embedding)
        
        # Handle legacy format (just the embedding array)
        elif isinstance(data, list):
            logger.info("Using cached intent embedding (legacy format)")
            return self._ensure_float_list(data)
        
        return None
    
    def _generate_intent_embedding(self, intent_text: str, cache: UnifiedCache, cache_key: str) -> List[float]:
        """Generate new intent embedding and cache it"""
        try:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=intent_text)
            embedding = response.data[0].embedding
            
            # Store intent embedding with consistent structure
            intent_data = {
                'embedding': embedding,
                'embedding_model': 'text-embedding-3-small',
                'embedding_generated_at': datetime.now().isoformat(),
                'intent_text': intent_text,
                'intent_text_preview': intent_text[:200]
            }
            
            cache.put(cache_key, intent_data, {
                'type': 'intent',
                'text_preview': intent_text[:100]
            })
            
            logger.info("Created and cached new intent embedding")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate intent embedding: {e}")
            return []
    
    def _find_similar_content(self, intent_embedding: List[float], chunks: List[DocumentChunk], 
                             cache_dir: Path) -> List[DocumentChunk]:
        """Find chunks similar to intent embedding"""
        if not intent_embedding:
            return chunks[:10]
        
        cache = UnifiedCache(cache_dir)
        ChunkData = namedtuple('ChunkData', ['chunk', 'score'])
        
        # Generate embeddings and calculate scores
        chunk_data = self._generate_embeddings_and_scores(chunks, intent_embedding, cache)
        
        # Print base scores if debug mode
        if self.config.debug_similarity and chunk_data:
            self._print_base_scores(chunk_data)
        
        # Apply boosts
        boosted_scores = self._apply_boosts(chunk_data)
        
        # Print debug info if enabled
        if self.config.debug_similarity and boosted_scores:
            self._print_full_debug_info(chunk_data, boosted_scores)
        
        # Sort and return
        sorted_chunks = sorted(boosted_scores.items(), key=lambda x: x[1], reverse=True)
        return [chunk_data[chunk_id].chunk for chunk_id, _ in sorted_chunks]
    
    def _generate_embeddings_and_scores(self, chunks: List[DocumentChunk], 
                                       intent_embedding: List[float], 
                                       cache: UnifiedCache) -> Dict:
        """Generate embeddings for chunks and calculate similarity scores"""
        ChunkData = namedtuple('ChunkData', ['chunk', 'score'])
        chunk_data = {}
        
        # Track cache performance
        stats = self._initialize_embedding_stats()
        
        # Process each chunk
        for chunk in chunks:
            embedding = self._get_or_generate_embedding(chunk, cache, stats)
            
            if embedding:
                score = self._cosine_similarity(intent_embedding, embedding)
                chunk_data[chunk.chunk_id] = ChunkData(chunk, score)
        
        # Log cache performance
        self._log_embedding_stats(stats, len(chunks))
        
        return chunk_data
    
    def _initialize_embedding_stats(self) -> Dict[str, int]:
        """Initialize embedding statistics tracking"""
        return {
            'from_cache': 0,
            'generated': 0,
            'already_loaded': 0
        }
    
    def _get_or_generate_embedding(self, chunk: DocumentChunk, cache: UnifiedCache, 
                                  stats: Dict[str, int]) -> Optional[List[float]]:
        """Get embedding from chunk, cache, or generate new one"""
        # Check if chunk already has embedding
        if chunk.embedding:
            stats['already_loaded'] += 1
            return chunk.embedding
        
        # Try to load from cache
        embedding = self._load_embedding_from_cache(chunk, cache)
        if embedding:
            chunk.embedding = embedding
            stats['from_cache'] += 1
            return embedding
        
        # Generate new embedding
        embedding = self._generate_new_embedding(chunk, cache)
        if embedding:
            chunk.embedding = embedding
            stats['generated'] += 1
            return embedding
        
        return None
    
    def _load_embedding_from_cache(self, chunk: DocumentChunk, cache: UnifiedCache) -> Optional[List[float]]:
        """Load embedding from cache if available"""
        cached_entry = cache.get(chunk.chunk_id)
        if not cached_entry or 'data' not in cached_entry:
            return None
            
        chunk_data = cached_entry['data']
        
        # Check if this is a unified structure with embedding
        if isinstance(chunk_data, dict) and 'embedding' in chunk_data:
            embedding = chunk_data.get('embedding')
            if embedding:
                logger.debug(f"Loaded embedding from cache for chunk {chunk.chunk_id}")
                # Ensure it's a list of floats
                return self._ensure_float_list(embedding)
        
        return None
    
    def _generate_new_embedding(self, chunk: DocumentChunk, cache: UnifiedCache) -> Optional[List[float]]:
        """Generate new embedding using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk.embedding_content[:8000]
            )
            embedding = response.data[0].embedding
            
            # Cache the embedding
            self._cache_embedding(chunk, embedding, cache)
            
            logger.debug(f"Generated and cached new embedding for chunk {chunk.chunk_id}")
            return embedding
            
        except Exception as e:
            logger.warning(f"Failed to generate embedding for chunk {chunk.chunk_id}: {e}")
            return None
    
    def _cache_embedding(self, chunk: DocumentChunk, embedding: List[float], cache: UnifiedCache) -> None:
        """Cache embedding with metadata"""
        # Get existing cached entry
        cached_entry = cache.get(chunk.chunk_id)
        
        if cached_entry and 'data' in cached_entry:
            # Update existing unified structure
            chunk_data = cached_entry['data']
            if isinstance(chunk_data, dict):
                # Update embedding fields
                chunk_data['embedding'] = embedding
                chunk_data['embedding_model'] = 'text-embedding-3-small'
                chunk_data['embedding_generated_at'] = datetime.now().isoformat()
                
                # Update metadata
                existing_meta = cached_entry.get('meta', {})
                updated_meta = {
                    **existing_meta,
                    'has_embedding': True,
                    'embedding_updated_at': datetime.now().isoformat()
                }
                
                # Save updated structure
                cache.put(chunk.chunk_id, chunk_data, updated_meta)
                return
        
        # Fallback: create minimal structure if chunk doesn't exist (shouldn't happen normally)
        logger.warning(f"Chunk {chunk.chunk_id} not found in cache, creating minimal entry with embedding")
        minimal_data = {
            'chunk_id': chunk.chunk_id,
            'embedding': embedding,
            'embedding_model': 'text-embedding-3-small',
            'embedding_generated_at': datetime.now().isoformat(),
            'embedding_content': chunk.embedding_content,
            'file_path': chunk.file_path,
            'heading_path': chunk.heading_path
        }
        
        cache.put(chunk.chunk_id, minimal_data, {
            'type': 'chunk',
            'has_embedding': True,
            'minimal_entry': True
        })
    
    def _log_embedding_stats(self, stats: Dict[str, int], total_chunks: int) -> None:
        """Log embedding generation statistics"""
        logger.info(f"Embedding cache performance: {stats['already_loaded']} already loaded, "
                   f"{stats['from_cache']} loaded from cache, {stats['generated']} generated "
                   f"(total: {total_chunks} chunks)")
    
    def _print_full_debug_info(self, chunk_data: Dict, boosted_scores: Dict) -> None:
        """Print complete debug information for similarity analysis"""
        # Group chunks by file
        chunks_by_file = defaultdict(list)
        for data in chunk_data.values():
            chunks_by_file[data.chunk.file_id].append(data)
        
        # Calculate file relevance
        file_relevance = self._calculate_file_relevance(chunks_by_file)
        
        # Print debug visualizations
        self._print_file_analysis(chunks_by_file)
        self._print_boost_details(chunk_data, file_relevance, boosted_scores)
        self._print_score_transformation(chunk_data, boosted_scores)
        self._print_strategy_insights(boosted_scores, chunk_data)
    
    def _calculate_file_relevance(self, chunks_by_file: Dict) -> Dict[str, float]:
        """Calculate average relevance score for each file"""
        return {
            file_id: sum(data.score for data in chunks_list) / len(chunks_list) 
            for file_id, chunks_list in chunks_by_file.items()
        }
    
    def _cosine_similarity(self, vector_a, vector_b):
        """Calculate cosine similarity between two vectors"""
        if not vector_a or not vector_b:
            return 0
        
        # Ensure vectors are lists of floats
        vector_a = self._ensure_float_list(vector_a)
        vector_b = self._ensure_float_list(vector_b)
        
        # Calculate dot product
        dot_product = self._calculate_dot_product(vector_a, vector_b)
        
        # Calculate magnitudes
        magnitude_a = self._calculate_vector_magnitude(vector_a)
        magnitude_b = self._calculate_vector_magnitude(vector_b)
        
        # Avoid division by zero
        if magnitude_a == 0 or magnitude_b == 0:
            return 0
        
        # Calculate cosine similarity
        return dot_product / (magnitude_a * magnitude_b)
    
    def _ensure_float_list(self, vector):
        """Ensure vector is a list of floats"""
        if isinstance(vector, str):
            # If it's a string representation of a list, parse it
            try:
                import ast
                vector = ast.literal_eval(vector)
            except:
                logger.error(f"Failed to parse vector string: {vector[:100]}...")
                return []
        
        # Ensure all elements are floats
        try:
            return [float(x) for x in vector]
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to convert vector to floats: {e}")
            return []
    
    def _calculate_dot_product(self, vector_a: List[float], vector_b: List[float]) -> float:
        """Calculate dot product of two vectors"""
        return sum(val_a * val_b for val_a, val_b in zip(vector_a, vector_b))
    
    def _calculate_vector_magnitude(self, vector: List[float]) -> float:
        """Calculate magnitude of a vector"""
        sum_of_squares = sum(val * val for val in vector)
        return sum_of_squares ** 0.5
    
    def _apply_boosts(self, chunk_scores: Dict) -> Dict:
        """Apply contextual boosts to chunk scores"""
        # Calculate file relevance
        file_relevance = self._calculate_file_relevance_scores(chunk_scores)
        
        # Apply boosts to each chunk
        boosted = {}
        for chunk_id, (chunk, score) in chunk_scores.items():
            boost = self._calculate_total_boost(chunk, score, chunk_scores, file_relevance)
            boosted[chunk_id] = score + boost
        
        return boosted
    
    def _calculate_file_relevance_scores(self, chunk_scores: Dict) -> Dict[str, float]:
        """Calculate average relevance score for each file"""
        file_scores = defaultdict(list)
        for chunk_id, (chunk, score) in chunk_scores.items():
            file_scores[chunk.file_id].append(score)
        
        return {file_id: sum(scores)/len(scores) for file_id, scores in file_scores.items()}
    
    def _calculate_total_boost(self, chunk, base_score: float, chunk_scores: Dict, 
                              file_relevance: Dict) -> float:
        """Calculate total boost for a chunk"""
        boost = 0
        
        # Add file context boost
        boost += self._calculate_file_boost(chunk, file_relevance)
        
        # Add proximity boosts
        boost += self._calculate_proximity_boosts(chunk, chunk_scores)
        
        # Add parent section boost
        boost += self._calculate_parent_boost(chunk, chunk_scores)
        
        return boost
    
    def _calculate_file_boost(self, chunk, file_relevance: Dict) -> float:
        """Calculate file context boost"""
        file_avg = file_relevance.get(chunk.file_id, 0)
        if file_avg <= 0.5:
            return 0
        return 0.1 * file_avg
    
    def _calculate_proximity_boosts(self, chunk, chunk_scores: Dict) -> float:
        """Calculate proximity-based boosts"""
        boost = 0
        
        # Previous chunk boost
        if chunk.prev_chunk_id in chunk_scores:
            prev_score = chunk_scores[chunk.prev_chunk_id][1]
            if prev_score > 0.6:
                boost += 0.05
        
        # Next chunk boost
        if chunk.next_chunk_id in chunk_scores:
            next_score = chunk_scores[chunk.next_chunk_id][1]
            if next_score > 0.6:
                boost += 0.05
        
        return boost
    
    def _calculate_parent_boost(self, chunk, chunk_scores: Dict) -> float:
        """Calculate parent section boost"""
        if not chunk.parent_heading_chunk_id:
            return 0
            
        if chunk.parent_heading_chunk_id not in chunk_scores:
            return 0
            
        parent_score = chunk_scores[chunk.parent_heading_chunk_id][1]
        if parent_score > 0.7:
            return 0.03
            
        return 0
    
    def _generate_strategy(self, config: Config, materials: List[Dict], 
                          similar_chunks: List[DocumentChunk]) -> ContentStrategy:
        """Generate content strategy based on gap analysis"""
        materials_summary = "\n".join([
            f"• {material.get('main_topic', 'Unknown')}: {material.get('summary', 'N/A')[:200]}"
            for material in materials
        ])
        
        # Prepare semantic matches for the prompt (file-level with embedded chunks)
        semantic_matches = self._prepare_semantic_matches(similar_chunks)
        
        # Prepare top individual chunks (chunk-level detail)
        top_chunks = self._prepare_top_chunks(similar_chunks[:20])
        
        # Prepare chunk clustering for gap analysis
        chunk_clusters = self._cluster_chunks_by_topic(similar_chunks[:50])
        
        # Load content standards
        content_standards = self._load_content_standards()
        
        prompt = get_unified_content_strategy_prompt(
            config, 
            materials_summary, 
            semantic_matches, 
            content_standards,
            top_chunks,
            chunk_clusters
        )
        system = UNIFIED_CONTENT_STRATEGY_SYSTEM
        
        try:
            result = self.llm_call(system, prompt, "gpt-4o")
            self.save_interaction(prompt, result, "content_strategy", "./llm_outputs/content_strategy")
            return ContentStrategy(
                result.get('thinking', ''),
                result.get('decisions', []),
                result.get('confidence', 0.5),
                result.get('summary', 'Strategy generated')
            )
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return ContentStrategy("Strategy generation failed", [], 0.0, "Strategy generation failed") 