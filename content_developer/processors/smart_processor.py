"""
Base processor class for AI Content Developer
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils import write, save_json, mkdir


class SmartProcessor:
    """Base class for all content processors"""
    
    def __init__(self, client, config):
        """Initialize processor with OpenAI client and config"""
        self.client = client
        self.config = config
    
    def process(self, *args, **kwargs):
        """Public process method"""
        return self._process(*args, **kwargs)
    
    def _process(self, *args, **kwargs):
        """Abstract method to be implemented by subclasses"""
        raise NotImplementedError
    
    def llm_call(self, system: str, user: str, model: str = "gpt-4o-mini") -> Dict:
        """Make LLM API call with JSON response format"""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    def _call_llm(self, messages: List[Dict[str, str]], 
                  model: str = "gpt-4o", 
                  response_format: Optional[str] = None) -> Dict:
        """Make LLM API call with messages format
        
        Used by generation processors for more control over conversation
        """
        kwargs = self._build_llm_kwargs(messages, model, response_format)
        response = self.client.chat.completions.create(**kwargs)
        
        return self._parse_llm_response(response, response_format)
    
    def _build_llm_kwargs(self, messages: List[Dict[str, str]], model: str, 
                         response_format: Optional[str]) -> Dict:
        """Build keyword arguments for LLM call"""
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.3
        }
        
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        
        return kwargs
    
    def _parse_llm_response(self, response, response_format: Optional[str]) -> Dict:
        """Parse LLM response based on expected format"""
        content = response.choices[0].message.content
        
        if response_format == "json_object":
            return json.loads(content)
        
        return {"content": content}
    
    def save_interaction(self, prompt: str, response: Any, operation: str, 
                        output_dir: str, source: str = ""):
        """Save LLM interaction for debugging and auditing"""
        # Prepare file paths
        base_path = self._prepare_output_path(output_dir, operation, source)
        
        # Save both prompt and response
        self._save_prompt_to_file(base_path, prompt, operation)
        self._save_response_to_file(base_path, response, operation)
    
    def _prepare_output_path(self, output_dir: str, operation: str, source: str) -> Path:
        """Prepare output directory and return base path for files"""
        # Ensure output directory exists
        self._ensure_directory_exists(output_dir)
        
        # Generate filename components
        timestamp = self._generate_timestamp()
        safe_source = self._sanitize_source_name(source, operation)
        
        # Construct base path
        return Path(output_dir) / f"{timestamp}_{safe_source}"
    
    def _ensure_directory_exists(self, directory: str) -> None:
        """Create directory if it doesn't exist"""
        mkdir(directory)
    
    def _generate_timestamp(self) -> str:
        """Generate timestamp for file naming"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _sanitize_source_name(self, source: str, fallback: str) -> str:
        """Sanitize source name for safe file naming"""
        if not source:
            return fallback
        
        # Remove unsafe characters and limit length
        safe_name = re.sub(r'[^\w\s-]', '_', source)
        return safe_name[:50]
    
    def _save_prompt_to_file(self, base_path: Path, prompt: str, operation: str) -> None:
        """Save prompt content to text file"""
        prompt_content = self._format_prompt_content(prompt, operation)
        write(base_path.with_suffix('.txt'), prompt_content)
    
    def _save_response_to_file(self, base_path: Path, response: Any, operation: str) -> None:
        """Save response data to JSON file"""
        response_data = self._format_response_data(response, operation)
        save_json(base_path.with_suffix('.json'), response_data)
    
    def _format_prompt_content(self, prompt: str, operation: str) -> str:
        """Format prompt content with metadata header"""
        header = f"=== {operation.upper()} ===\n"
        header += f"{datetime.now().isoformat()}\n"
        header += f"{'='*50}\n\n"
        return header + prompt
    
    def _format_response_data(self, response: Any, operation: str) -> Dict[str, Any]:
        """Format response data with metadata"""
        return {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation
                },
                "data": response
            }