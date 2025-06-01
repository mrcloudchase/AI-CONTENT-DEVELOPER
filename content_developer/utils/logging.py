"""
Logging configuration for AI Content Developer
"""
import logging
import sys
from pathlib import Path


def setup_logging(log_dir: str = "./llm_outputs") -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'{log_dir}/acd.log', mode='a')
        ]
    )
    
    return logging.getLogger('ContentDeveloper') 