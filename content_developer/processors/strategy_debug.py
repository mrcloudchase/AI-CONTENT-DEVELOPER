"""
Debug visualization methods for ContentStrategyProcessor
"""
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class StrategyDebugMixin:
    """Mixin class providing debug visualization methods for strategy processing"""
    
    def _print_debug_header(self, title: str, width: int = 80):
        """Print a formatted debug header"""
        print(f"\n{'=' * width}")
        print(f"{title.center(width)}")
        print(f"{'=' * width}")
    
    def _print_base_scores(self, chunk_data: Dict, limit: int = 20):
        """Print base similarity scores table"""
        self._print_debug_header("BASE SIMILARITY SCORES")
        print(f"Showing top {limit} chunks by raw similarity:\n")
        
        # Sort by base score
        sorted_chunks = sorted(chunk_data.items(), key=lambda x: x[1].score, reverse=True)[:limit]
        
        # Print header
        print(f"{'#':>3} | {'File':<35} | {'Section':<35} | {'Score':>7}")
        print(f"{'-'*3}-+-{'-'*35}-+-{'-'*35}-+-{'-'*7}")
        
        # Print rows
        for i, (chunk_id, data) in enumerate(sorted_chunks, 1):
            file_name = Path(data.chunk.file_path).name[:33]
            section = ' > '.join(data.chunk.heading_path)[:33] if data.chunk.heading_path else "Main"
            print(f"{i:>3} | {file_name:<35} | {section:<35} | {data.score:>7.3f}")
    
    def _print_file_analysis(self, chunks_by_file: Dict):
        """Print file-level relevance analysis"""
        self._print_debug_header("FILE-LEVEL RELEVANCE")
        
        # Calculate file stats
        file_stats = self._calculate_file_stats(chunks_by_file)
        
        # Sort by average score
        file_stats.sort(key=lambda x: x[2], reverse=True)
        
        # Print table
        self._print_file_stats_table(file_stats[:10])
    
    def _calculate_file_stats(self, chunks_by_file: Dict) -> List[tuple]:
        """Calculate statistics for each file"""
        file_stats = []
        
        for file_id, file_chunks in chunks_by_file.items():
            if not file_chunks:  # Skip files without chunks
                continue
                
            file_path = file_chunks[0].chunk.file_path
            file_name = Path(file_path).name
            avg_score = sum(data.score for data in file_chunks) / len(file_chunks)
            relevance = self._determine_relevance_level(avg_score)
            
            file_stats.append((file_name, len(file_chunks), avg_score, relevance))
        
        return file_stats
    
    def _determine_relevance_level(self, avg_score: float) -> str:
        """Determine relevance level based on average score"""
        if avg_score > 0.7:
            return "HIGH ⬆️"
        if avg_score > 0.5:
            return "MEDIUM ↗️"
        if avg_score > 0.3:
            return "LOW →"
        return "MINIMAL ↘️"
    
    def _print_file_stats_table(self, file_stats: List[tuple]):
        """Print file statistics table"""
        print(f"\n{'File':<35} | {'Chunks':>7} | {'Avg Score':>9} | {'Relevance':<12}")
        print(f"{'-'*35}-+-{'-'*7}-+-{'-'*9}-+-{'-'*12}")
        
        for file_name, chunk_count, avg_score, relevance in file_stats:
            print(f"{file_name[:33]:<35} | {chunk_count:>7} | {avg_score:>9.3f} | {relevance:<12}")
    
    def _print_boost_details(self, chunk_data: Dict, file_relevance: Dict, boosted_scores: Dict, limit: int = 10):
        """Print detailed boost calculations"""
        self._print_debug_header("BOOST CALCULATIONS (Top 10)")
        
        # Get top chunks by boosted score
        top_chunks = sorted(boosted_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        for i, (chunk_id, final_score) in enumerate(top_chunks, 1):
            self._print_chunk_boost_details(i, chunk_id, final_score, chunk_data, file_relevance)
    
    def _print_chunk_boost_details(self, index: int, chunk_id: str, final_score: float,
                                  chunk_data: Dict, file_relevance: Dict):
        """Print boost details for a single chunk"""
        data = chunk_data[chunk_id]
        chunk = data.chunk
        base_score = data.score
        
        print(f"\nChunk #{index}: {Path(chunk.file_path).name} > {' > '.join(chunk.heading_path)}")
        print(f"├─ Base Score: {base_score:.3f}")
        
        # File boost
        self._print_file_boost(chunk, file_relevance)
        
        # Proximity boosts
        self._print_proximity_boosts(chunk, chunk_data)
        
        # Parent boost
        self._print_parent_boost(chunk, chunk_data)
        
        print(f"└─ FINAL SCORE: {final_score:.3f} {'⭐' if index == 1 else ''}")
    
    def _print_file_boost(self, chunk, file_relevance: Dict):
        """Print file-level boost information"""
        file_avg = file_relevance.get(chunk.file_id, 0)
        if file_avg <= 0.5:
            return
            
        file_boost = 0.1 * file_avg
        print(f"├─ File Boost: +{file_boost:.3f} (file avg: {file_avg:.3f} > 0.5 threshold)")
    
    def _print_proximity_boosts(self, chunk, chunk_data: Dict):
        """Print proximity boost information"""
        print(f"├─ Proximity Boosts:")
        
        # Previous chunk boost
        if chunk.prev_chunk_id and chunk.prev_chunk_id in chunk_data:
            prev_score = chunk_data[chunk.prev_chunk_id].score
            if prev_score > 0.6:
                print(f"│  ├─ Previous chunk: {prev_score:.3f} > 0.6 → +0.05")
        
        # Next chunk boost
        if chunk.next_chunk_id and chunk.next_chunk_id in chunk_data:
            next_score = chunk_data[chunk.next_chunk_id].score
            if next_score > 0.6:
                print(f"│  └─ Next chunk: {next_score:.3f} > 0.6 → +0.05")
    
    def _print_parent_boost(self, chunk, chunk_data: Dict):
        """Print parent section boost information"""
        if not chunk.parent_heading_chunk_id:
            return
            
        if chunk.parent_heading_chunk_id not in chunk_data:
            return
            
        parent_score = chunk_data[chunk.parent_heading_chunk_id].score
        if parent_score > 0.7:
            print(f"├─ Parent Boost: +0.03 (parent: {parent_score:.3f} > 0.7)")
    
    def _print_score_transformation(self, chunk_data: Dict, boosted_scores: Dict, limit: int = 15):
        """Print score transformation visualization"""
        self._print_debug_header("SCORE TRANSFORMATION")
        print(f"\n{'Chunk':<40} | {'Base':>6} → {'Final':>6} | {'Change':>6} | {'%':>5}")
        print(f"{'-'*40}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*5}")
        
        # Get chunks sorted by boost amount
        transformations = []
        for chunk_id, final_score in boosted_scores.items():
            base_score = chunk_data[chunk_id].score
            boost = final_score - base_score
            boost_pct = (boost / base_score * 100) if base_score > 0 else 0
            chunk = chunk_data[chunk_id].chunk
            chunk_name = f"{Path(chunk.file_path).name[:20]} > {chunk.heading_path[0][:15] if chunk.heading_path else 'Main'}"
            transformations.append((chunk_name, base_score, final_score, boost, boost_pct))
        
        # Sort by boost percentage
        transformations.sort(key=lambda x: x[4], reverse=True)
        
        for chunk_name, base, final, boost, pct in transformations[:limit]:
            arrow = "⬆️" if boost > 0 else "→"
            print(f"{chunk_name:<40} | {base:>6.3f} → {final:>6.3f} | {boost:>+6.3f} | {arrow} {pct:>3.0f}%")
    
    def _print_strategy_insights(self, boosted_scores: Dict, chunk_data: Dict):
        """Print insights about how scores relate to strategy"""
        self._print_debug_header("CONTENT STRATEGY INSIGHTS")
        
        # Categorize scores
        categories = self._categorize_scores(boosted_scores)
        
        # Print category details
        self._print_relevance_category(categories['high'], chunk_data, "HIGH", "0.8+")
        self._print_relevance_category(categories['medium'], chunk_data, "MEDIUM", "0.5-0.8")
        self._print_relevance_category(categories['low'], chunk_data, "LOW", "<0.5")
        
        # Print recommendations
        self._print_strategy_recommendations()
        
        # Show distribution
        total_chunks = len(boosted_scores)
        if total_chunks > 0:
            self._print_score_distribution(categories, total_chunks)
    
    def _categorize_scores(self, boosted_scores: Dict) -> Dict[str, List[tuple]]:
        """Categorize scores into high, medium, and low relevance"""
        return {
            'high': [(cid, score) for cid, score in boosted_scores.items() if score > 0.8],
            'medium': [(cid, score) for cid, score in boosted_scores.items() if 0.5 < score <= 0.8],
            'low': [(cid, score) for cid, score in boosted_scores.items() if score <= 0.5]
        }
    
    def _print_relevance_category(self, category_items: List[tuple], chunk_data: Dict, 
                                 level_name: str, score_range: str):
        """Print details for a relevance category"""
        print(f"\n{level_name} RELEVANCE ({score_range}): {len(category_items)} chunks")
        
        if level_name == "HIGH":
            self._print_high_relevance_details(category_items, chunk_data)
        elif level_name == "MEDIUM":
            self._print_medium_relevance_details()
        elif level_name == "LOW":
            self._print_low_relevance_details()
    
    def _print_high_relevance_details(self, high_relevance: List[tuple], chunk_data: Dict):
        """Print details for high relevance chunks"""
        if not high_relevance:
            return
            
        topics = set()
        files = set()
        
        for cid, _ in high_relevance[:5]:
            chunk = chunk_data[cid].chunk
            if chunk.heading_path:
                topics.add(chunk.heading_path[0])
            files.add(Path(chunk.file_path).name)
        
        print(f"→ Topics well-covered: {', '.join(list(topics)[:3])}")
        print(f"→ Files with matches: {', '.join(list(files)[:3])}")
        print(f"→ Strategy: UPDATE these sections with specific enhancements")
        print(f"→ Intent alignment: Content exists that closely matches your materials")
    
    def _print_medium_relevance_details(self):
        """Print details for medium relevance chunks"""
        print(f"→ Topics partially covered: Related content exists")
        print(f"→ Strategy: ENHANCE with new specific details from materials")
        print(f"→ Intent alignment: Some overlap but missing key aspects")
    
    def _print_low_relevance_details(self):
        """Print details for low relevance chunks"""
        print(f"→ Gap identified: Content not well covered")
        print(f"→ Strategy: CREATE new dedicated documentation")
        print(f"→ Intent alignment: Materials cover topics not in existing content")
    
    def _print_strategy_recommendations(self):
        """Print strategy recommendations"""
        print(f"\nRECOMMENDED ACTIONS:")
        print(f"Based on similarity distribution, expect:")
        print(f"- CREATE actions for gaps (low similarity areas)")
        print(f"- UPDATE actions for high similarity areas needing enhancement")
    
    def _print_score_distribution(self, categories: Dict[str, List[tuple]], total_chunks: int):
        """Print score distribution and interpretation"""
        high_count = len(categories['high'])
        medium_count = len(categories['medium'])
        low_count = len(categories['low'])
        
        print(f"\nSCORE DISTRIBUTION:")
        print(f"├─ High (0.8+):   {high_count:>3} chunks ({high_count/total_chunks*100:>5.1f}%)")
        print(f"├─ Medium (0.5-0.8): {medium_count:>3} chunks ({medium_count/total_chunks*100:>5.1f}%)")
        print(f"└─ Low (<0.5):    {low_count:>3} chunks ({low_count/total_chunks*100:>5.1f}%)")
        
        # Provide interpretation
        print(f"\nINTERPRETATION:")
        if high_count / total_chunks > 0.3:
            print("→ Strong existing coverage - expect mostly UPDATE actions")
        elif low_count / total_chunks > 0.7:
            print("→ Significant content gaps - expect mostly CREATE actions")
        else:
            print("→ Mixed coverage - expect both CREATE and UPDATE actions") 