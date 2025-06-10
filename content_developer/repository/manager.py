"""
Repository management for cloning and updating git repositories
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manage git repository operations"""
    
    @staticmethod
    def extract_name(url: str) -> str:
        """Extract repository name from URL"""
        # Remove trailing .git and slashes
        cleaned_url = url.rstrip('.git').rstrip('/')
        
        # Parse URL and extract path
        parsed_url = urlparse(cleaned_url)
        url_path = parsed_url.path.rstrip('/')
        
        # Get last component of path
        path_components = url_path.split('/')
        repo_name = path_components[-1] if path_components else "repo"
        
        # Default to "repo" if empty
        return repo_name or "repo"
    
    def clone_or_update(self, repo_url: str, work_dir: Path) -> Path:
        """Clone or update repository"""
        repo_name = self.extract_name(repo_url)
        repo_path = work_dir / repo_name
        
        if repo_path.exists():
            return self._update_repo(repo_path, repo_url)
        else:
            return self._clone_repo(repo_url, repo_path)
    
    def _run_git(self, cmd: List[str], cwd: Path = None):
        """Run git command"""
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    
    def _update_repo(self, repo_path: Path, repo_url: str) -> Path:
        """Update existing repository"""
        logger.info(f"Updating repository at {repo_path}")
        try:
            self._run_git(["git", "fetch"], repo_path)
            self._run_git(["git", "pull"], repo_path)
            logger.info("Repository updated successfully")
            return repo_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update repo: {e}")
            return repo_path
    
    def _clone_repo(self, repo_url: str, repo_path: Path) -> Path:
        """Clone new repository"""
        logger.info(f"Cloning {repo_url} to {repo_path}")
        self._run_git(["git", "clone", repo_url, str(repo_path)])
        logger.info("Repository cloned successfully")
        return repo_path
    
    @staticmethod
    def _count_md_files(path: Path) -> int:
        """Count markdown files in a directory (non-recursive)"""
        try:
            return len([f for f in path.iterdir() if f.is_file() and f.suffix.lower() == '.md'])
        except:
            return 0
    
    @staticmethod
    def _has_toc(path: Path) -> bool:
        """Check if directory has TOC.yml"""
        return (path / "TOC.yml").exists() or (path / "toc.yml").exists()
    
    @staticmethod
    def _should_skip_directory(dir_name: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            'node_modules', 'dist', 'build', 'target', '.git', 
            'test', 'tests', '__pycache__', 'coverage', 'media', 
            'images', 'assets', 'static', 'vendor', 'dependencies'
        }
        return dir_name.lower() in skip_dirs
    
    def get_directory_structure(self, repo_path: Path, max_depth: int = 3) -> str:
        """Get repository directory structure with markdown file counts"""
        lines = []
        
        # Add repository root info
        root_md_count = self._count_md_files(repo_path)
        root_toc = " [TOC]" if self._has_toc(repo_path) else ""
        lines.append(f"[Repository Root]{root_toc} ({root_md_count} .md)")
        
        # Build directory tree
        self._add_directory_tree(repo_path, lines, "", 0, max_depth)
        
        return "\n".join(lines)
    
    def _add_directory_tree(self, path: Path, lines: List[str], prefix: str, 
                           depth: int, max_depth: int) -> None:
        """Add directory tree to lines list"""
        if depth > max_depth:
            return
        
        # Get only directories
        directories = self._get_valid_directories(path)
        
        for i, dir_item in enumerate(directories):
            is_last = i == len(directories) - 1
            self._add_directory_line(dir_item, lines, prefix, is_last)
            
            # Recurse into subdirectories
            extension = "    " if is_last else "│   "
            self._add_directory_tree(dir_item, lines, prefix + extension, 
                                   depth + 1, max_depth)
    
    def _get_valid_directories(self, path: Path) -> List[Path]:
        """Get list of valid directories to display"""
        try:
            dirs = [item for item in sorted(path.iterdir(), key=lambda x: x.name) 
                   if item.is_dir() and not item.name.startswith('.')]
            
            # Filter out directories we should skip
            return [d for d in dirs if not self._should_skip_directory(d.name)]
        except:
            return []
    
    def _add_directory_line(self, dir_item: Path, lines: List[str], 
                           prefix: str, is_last: bool) -> None:
        """Add a single directory line to the output"""
        current = "└── " if is_last else "├── "
        
        # Count markdown files and check for TOC
        md_count = self._count_md_files(dir_item)
        toc_indicator = " [TOC]" if self._has_toc(dir_item) else ""
        md_indicator = f" ({md_count} .md)" if md_count > 0 else ""
        
        # Show directory with indicators
        lines.append(f"{prefix}{current}{dir_item.name}{toc_indicator}{md_indicator}")
    
    def get_structure(self, repo_path: Path, max_depth: int = 3, show_files: bool = False) -> str:
        """Get repository structure as string
        
        Args:
            repo_path: Path to repository
            max_depth: Maximum depth to traverse
            show_files: Ignored (always shows directories only for performance)
            
        Returns:
            Tree structure as string
        """
        # Always use directory-only structure for better performance
        return self.get_directory_structure(repo_path, max_depth)
    

 