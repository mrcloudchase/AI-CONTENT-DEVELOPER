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
    
    def get_directory_structure(self, repo_path: Path, max_depth: int = 3) -> str:
        """Get repository directory structure with markdown file counts"""
        lines = []
        
        def count_md_files(path: Path) -> int:
            """Count markdown files in a directory (non-recursive)"""
            try:
                return len([f for f in path.iterdir() if f.is_file() and f.suffix.lower() == '.md'])
            except:
                return 0
        
        def has_toc(path: Path) -> bool:
            """Check if directory has TOC.yml"""
            return (path / "TOC.yml").exists() or (path / "toc.yml").exists()
        
        def add_dir(path: Path, prefix: str = "", depth: int = 0, parent_shown: bool = True):
            if depth > max_depth:
                return
            
            # Get only directories
            dirs = [item for item in sorted(path.iterdir(), key=lambda x: x.name) 
                   if item.is_dir() and not item.name.startswith('.')]
            
            # Skip common non-documentation directories
            skip_dirs = {'node_modules', 'dist', 'build', 'target', '.git', 
                        'test', 'tests', '__pycache__', 'coverage', 'media', 
                        'images', 'assets', 'static', 'vendor', 'dependencies'}
            
            dirs = [d for d in dirs if d.name.lower() not in skip_dirs]
            
            for i, dir_item in enumerate(dirs):
                is_last = i == len(dirs) - 1
                current = "└── " if is_last else "├── "
                
                # Count markdown files and check for TOC
                md_count = count_md_files(dir_item)
                toc_indicator = " [TOC]" if has_toc(dir_item) else ""
                md_indicator = f" ({md_count} .md)" if md_count > 0 else ""
                
                # Show directory with indicators
                lines.append(f"{prefix}{current}{dir_item.name}{toc_indicator}{md_indicator}")
                
                # Recurse into subdirectories
                extension = "    " if is_last else "│   "
                add_dir(dir_item, prefix + extension, depth + 1)
        
        # Add repository root info
        root_md_count = count_md_files(repo_path)
        root_toc = " [TOC]" if has_toc(repo_path) else ""
        lines.append(f"[Repository Root]{root_toc} ({root_md_count} .md)")
        
        # Start with repository contents
        add_dir(repo_path, "", 0)
        
        return "\n".join(lines)
    
    def get_structure(self, repo_path: Path, max_depth: int = 3, show_files: bool = False) -> str:
        """Get repository structure as string
        
        Args:
            repo_path: Path to repository
            max_depth: Maximum depth to traverse
            show_files: Whether to show files (only recommended for small repos)
            
        Returns:
            Tree structure as string
        """
        if show_files:
            return self.get_structure_with_files(repo_path, max_depth)
        else:
            # Default to directory-only structure for better performance
            return self.get_directory_structure(repo_path, max_depth)
    
    def get_structure_with_files(self, repo_path: Path, max_depth: int = 3) -> str:
        """Get repository structure including files (legacy method)"""
        lines = []
        
        def add_dir(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                if item.name.startswith('.'):
                    continue
                
                is_last = i == len(items) - 1
                current = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current}{item.name}")
                
                if item.is_dir():
                    extension = "    " if is_last else "│   "
                    add_dir(item, prefix + extension, depth + 1)
        
        # Start directly with repository contents
        add_dir(repo_path, "", 0)
        return "\n".join(lines)
    
    def get_condensed_structure(self, repo_path: Path, service_keywords: List[str] = None) -> str:
        """Get condensed structure for large repositories
        
        Args:
            repo_path: Path to repository
            service_keywords: Keywords to prioritize directories (e.g., ['aks', 'kubernetes'])
        
        Returns:
            Condensed directory structure focusing on documentation directories
        """
        lines = []
        doc_dirs = []
        
        def analyze_directory(path: Path, rel_path: str = "") -> dict:
            """Analyze a directory and return stats"""
            stats = {
                'path': rel_path or ".",
                'md_count': 0,
                'has_toc': False,
                'subdirs': 0,
                'doc_subdirs': 0,
                'relevance_score': 0
            }
            
            try:
                # Count markdown files
                md_files = [f for f in path.iterdir() if f.is_file() and f.suffix.lower() == '.md']
                stats['md_count'] = len(md_files)
                
                # Check for TOC
                stats['has_toc'] = (path / "TOC.yml").exists() or (path / "toc.yml").exists()
                
                # Count subdirectories with documentation
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        stats['subdirs'] += 1
                        # Quick check if subdir has .md files
                        if any(f.suffix.lower() == '.md' for f in item.iterdir() if f.is_file()):
                            stats['doc_subdirs'] += 1
                
                # Calculate relevance score
                if service_keywords:
                    path_lower = rel_path.lower()
                    for keyword in service_keywords:
                        if keyword.lower() in path_lower:
                            stats['relevance_score'] += 10
                
                # Boost score for documentation indicators
                if stats['has_toc']:
                    stats['relevance_score'] += 5
                if stats['md_count'] > 0:
                    stats['relevance_score'] += min(stats['md_count'], 20)  # Cap at 20
                
            except:
                pass
            
            return stats
        
        # First, scan top-level directories
        lines.append("=== CONDENSED REPOSITORY STRUCTURE ===")
        lines.append(f"Repository: {repo_path.name or repo_path.absolute().name}")
        lines.append("")
        
        # Analyze root
        root_stats = analyze_directory(repo_path)
        if root_stats['has_toc'] or root_stats['md_count'] > 5:
            lines.append(f"📁 [Root] - {root_stats['md_count']} docs{' [TOC]' if root_stats['has_toc'] else ''}")
            doc_dirs.append((".", root_stats))
        
        # Analyze top-level directories
        top_dirs = []
        for item in sorted(repo_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                # Skip non-doc directories
                if item.name.lower() in {'node_modules', 'dist', 'build', '.git', 'test', 'tests'}:
                    continue
                
                stats = analyze_directory(item, item.name)
                if stats['md_count'] > 0 or stats['doc_subdirs'] > 0:
                    top_dirs.append((item.name, stats))
        
        # Sort by relevance and documentation presence
        top_dirs.sort(key=lambda x: (x[1]['relevance_score'], x[1]['md_count'], x[1]['has_toc']), reverse=True)
        
        # Show top documentation directories
        lines.append("\n📚 Primary Documentation Directories:")
        for dir_name, stats in top_dirs[:10]:  # Show top 10
            toc = " [TOC]" if stats['has_toc'] else ""
            subdirs = f" ({stats['doc_subdirs']} subdirs)" if stats['doc_subdirs'] > 0 else ""
            lines.append(f"├── {dir_name}{toc} - {stats['md_count']} docs{subdirs}")
            
            # If this is a major doc directory, show its immediate subdirs
            if stats['has_toc'] and stats['doc_subdirs'] > 2:
                dir_path = repo_path / dir_name
                subdirs = []
                for subitem in sorted(dir_path.iterdir())[:5]:  # Limit to 5
                    if subitem.is_dir() and not subitem.name.startswith('.'):
                        sub_stats = analyze_directory(subitem, f"{dir_name}/{subitem.name}")
                        if sub_stats['md_count'] > 0:
                            subdirs.append((subitem.name, sub_stats))
                
                for i, (subdir_name, sub_stats) in enumerate(subdirs):
                    is_last = i == len(subdirs) - 1
                    prefix = "    └── " if is_last else "    ├── "
                    lines.append(f"{prefix}{subdir_name} ({sub_stats['md_count']} docs)")
        
        # Summary statistics
        lines.append("\n📊 Summary:")
        total_shown = min(len(top_dirs), 10)
        lines.append(f"- Showing {total_shown} of {len(top_dirs)} documentation directories")
        if len(top_dirs) > 10:
            lines.append(f"- {len(top_dirs) - 10} additional directories not shown")
        
        # Service-specific recommendations
        if service_keywords and any(stats['relevance_score'] > 0 for _, stats in top_dirs):
            lines.append(f"\n🎯 Directories matching service keywords {service_keywords}:")
            relevant = [(name, stats) for name, stats in top_dirs if stats['relevance_score'] > 0][:5]
            for name, stats in relevant:
                lines.append(f"- {name} (relevance: {stats['relevance_score']})")
        
        return "\n".join(lines) 