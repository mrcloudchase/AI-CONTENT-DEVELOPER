"""
Configuration model for AI Content Developer
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..utils import mkdir


@dataclass
class Config:
    """Configuration for content development workflow"""
    # Repository settings
    repo_url: str
    content_goal: str
    service_area: str
    
    # Audience settings
    audience: str = "technical professionals"
    audience_level: str = "intermediate"  # beginner | intermediate | advanced
    
    # Optional settings
    support_materials: List[str] = field(default_factory=list)
    auto_confirm: bool = False
    work_dir: Path = Path.cwd() / "work" / "tmp"
    max_repo_depth: int = 3
    content_limit: int = 15000
    phases: str = "3"
    debug_similarity: bool = False
    apply_changes: bool = False
    
    # API key loaded from environment
    api_key: str = ""
    
    def __post_init__(self):
        """Post-initialization setup"""
        self._validate_api_key()
        self._create_output_directories()
    
    def _validate_api_key(self):
        """Validate that OpenAI API key is available"""
        import os
        
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    def _create_output_directories(self):
        """Create all necessary output directories"""
        base_dir = "./llm_outputs"
        
        # Define all required directories
        required_directories = [
            "embeddings",
            "content_strategy", 
            "preview",
            "materials_summary",
            "decisions/working_directory",
            "content_generation/create",
            "content_generation/update",
            "content_discovery"
        ]
        
        # Create each directory
        for directory in required_directories:
            full_path = f"{base_dir}/{directory}"
            mkdir(full_path) 