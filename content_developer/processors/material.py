"""
Material processor for support materials
"""
from pathlib import Path
from typing import Dict, List, Optional
import logging

from ..extraction import ContentExtractor
from ..prompts import get_material_summary_prompt, MATERIAL_SUMMARY_SYSTEM
from .smart_processor import SmartProcessor

logger = logging.getLogger(__name__)


class MaterialProcessor(SmartProcessor):
    """Process support materials and generate summaries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = ContentExtractor(self.config)
    
    def _process(self, materials: List[str], repo_path: Path) -> List[Dict]:
        """Process list of materials and return summaries"""
        logger.info(f"MaterialProcessor._process called with {len(materials)} materials: {materials}")
        summaries = []
        for material in materials:
            if content := self.extractor.extract(material, repo_path):
                if summary := self._summarize(content, material):
                    summaries.append(summary)
        
        logger.info(f"Processed {len(summaries)}/{len(materials)} materials")
        return summaries
    
    def _summarize(self, content: str, source: str) -> Optional[Dict]:
        """Generate summary for material content"""
        prompt = get_material_summary_prompt(source, content)
        system = MATERIAL_SUMMARY_SYSTEM
        
        try:
            result = self.llm_call(system, prompt)
            self.save_interaction(
                prompt, 
                result, 
                "materials_summary", 
                "./llm_outputs/materials_summary", 
                source
            )
            return result
        except Exception as e:
            logger.error(f"Failed to summarize {source}: {e}")
            return None 