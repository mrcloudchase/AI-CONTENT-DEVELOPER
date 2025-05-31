#!/usr/bin/env python3
"""Hyper-Compact Phases 1, 2 & 3: Repository Analysis, Content Strategy & Generation"""
import argparse, json, os, sys, subprocess, shutil, re, logging, hashlib, yaml, threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps, reduce
from collections import defaultdict, namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import prompts from separate module
from prompts import (
    get_material_summary_prompt, MATERIAL_SUMMARY_SYSTEM,
    get_directory_selection_prompt, DIRECTORY_SELECTION_SYSTEM,
    get_unified_content_strategy_prompt, UNIFIED_CONTENT_STRATEGY_SYSTEM,
    get_create_content_prompt, CREATE_CONTENT_SYSTEM,
    get_update_content_prompt, UPDATE_CONTENT_SYSTEM
)

# === CONFIGURATION ===
DIRS = ["materials_summary", "decisions/working_directory", "content_strategy", "embeddings", 
        "content_generation/create", "content_generation/update", "materials_cache", "preview/create", "preview/update"]
IMPORTS = [
    ('openai', ['OpenAI'], True, "OpenAI required. Install: pip install openai"),
    ('rich.console', ['Console'], False, None),
    ('rich.panel', ['Panel'], False, None),
    ('docx', ['Document'], False, "python-docx not available"),
    ('PyPDF2', ['PdfReader'], False, "PyPDF2 not available"),
    ('requests', None, False, "requests not available"),
    ('bs4', ['BeautifulSoup'], False, "beautifulsoup4 not available"),
    ('tenacity', ['retry', 'stop_after_attempt', 'wait_exponential', 'retry_if_exception_type'], False, "tenacity not available - retry logic disabled"),
    ('rich.progress', ['Progress', 'SpinnerColumn', 'TextColumn', 'BarColumn', 'TaskProgressColumn', 'TimeRemainingColumn'], False, "Rich progress not available")
]

# === UTILITIES ===
compose = lambda *fns: lambda x: reduce(lambda v, f: f(v), fns, x)
pipe = lambda val, *fns: compose(*fns)(val)
safe_get = lambda d, *keys, default=None: reduce(lambda x, k: x.get(k, default) if isinstance(x, dict) else default, keys, d)
safe_call = lambda fn, *args, default=None: (lambda r: r if r is not None else default)(error_handler(fn)(*args))
get_hash = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()
chunk_text = lambda text, size=3000: [text[i:i+size] for i in range(0, len(text), size)]

def setup_logging():
    Path("./llm_outputs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                       handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('./llm_outputs/phase1.log', mode='a')])
    return logging.getLogger('ContentDeveloper')

def safe_import(module: str, items: List[str] = None, required: bool = False, msg: str = None):
    try:
        mod = __import__(module, fromlist=items or [])
        return tuple(getattr(mod, item) for item in items) if items else mod
    except ImportError:
        if msg and 'logger' in globals(): logger.warning(msg)
        if required: sys.exit(1)
        return tuple([None] * len(items)) if items else None

def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: return func(*args, **kwargs)
        except Exception as e: logger.error(f"Error in {func.__name__}: {e}"); return None
    return wrapper

# === SETUP ===
logger = setup_logging()

# Dynamic imports with configuration
globals_dict = {}
for module, items, required, msg in IMPORTS:
    if items:
        result = safe_import(module, items, required, msg)
        if result:
            for i, item in enumerate(items):
                globals_dict[item] = result[i]
                globals()[item] = result[i]
    else:
        result = safe_import(module, None, required, msg)
        if result:
            globals_dict[module.split('.')[-1]] = result
            globals()[module.split('.')[-1]] = result

# Check availability
HAS_OPENAI = 'OpenAI' in globals_dict
HAS_RICH = 'Console' in globals_dict and 'Panel' in globals_dict
HAS_DOCX = 'Document' in globals_dict
HAS_PDF = 'PdfReader' in globals_dict
HAS_WEB = 'requests' in globals_dict and 'BeautifulSoup' in globals_dict
HAS_TENACITY = 'retry' in globals_dict
HAS_PROGRESS = 'Progress' in globals_dict

# === FILE OPERATIONS ===
class FileOps:
    read = lambda self, p, limit=15000: Path(p).read_text()[:limit] if limit else Path(p).read_text()
    write = lambda self, p, content: Path(p).write_text(content)
    save_json = lambda self, p, data: Path(p).write_text(json.dumps(data, indent=2))
    load_json = lambda self, p: json.loads(Path(p).read_text()) if Path(p).exists() else {}
    get_hash = lambda self, p: hashlib.sha256(open(p, 'rb').read()).hexdigest() if Path(p).exists() else ""
    mkdir = lambda self, p: Path(p).mkdir(parents=True, exist_ok=True)

fileops = FileOps()

# === CACHE SYSTEM ===
class UnifiedCache:
    def __init__(self, base_path):
        self.path = Path(base_path)
        self.manifest_path = self.path / "manifest.json"
        self._lock = threading.Lock()
        fileops.mkdir(self.path)
        
        # Try to load manifest, recover if corrupted
        try:
            self.manifest = fileops.load_json(self.manifest_path)
        except Exception as e:
            logger.warning(f"Manifest corrupted, attempting recovery: {e}")
            self.manifest = self._recover_manifest()
    
    def _recover_manifest(self):
        """Recover manifest from existing cache files"""
        manifest = {}
        
        # Scan for all JSON files except manifest
        for json_file in self.path.glob("*.json"):
            if json_file.name == "manifest.json":
                continue
            
            try:
                data = fileops.load_json(json_file)
                chunk_id = json_file.stem
                
                # Add to manifest
                manifest[chunk_id] = {
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'meta': data.get('meta', {})
                }
            except Exception as e:
                logger.warning(f"Could not recover {json_file}: {e}")
        
        # Save recovered manifest
        fileops.save_json(self.manifest_path, manifest)
        logger.info(f"Recovered manifest with {len(manifest)} entries")
        return manifest
    
    def reload_manifest(self):
        """Reload manifest from disk with error recovery"""
        try:
            self.manifest = fileops.load_json(self.manifest_path)
        except Exception as e:
            logger.warning(f"Manifest reload failed, recovering: {e}")
            self.manifest = self._recover_manifest()
    
    def get(self, key):
        cache_file = self.path / f"{key}.json"
        try:
            return fileops.load_json(cache_file) if cache_file.exists() else None
        except Exception as e:
            logger.warning(f"Cache file {key} corrupted: {e}")
            return None
    
    def put(self, key, data, meta=None):
        with self._lock:
            try:
                cache_file = self.path / f"{key}.json"
                fileops.save_json(cache_file, {'data': data, 'meta': meta or {}, 'timestamp': datetime.now().isoformat()})
                # Reload manifest to get latest changes
                self.reload_manifest()
                self.manifest[key] = {'timestamp': datetime.now().isoformat(), 'meta': meta}
                fileops.save_json(self.manifest_path, self.manifest)
            except Exception as e:
                logger.error(f"Failed to save cache entry {key}: {e}")
    
    def update_manifest_entry(self, key, value):
        """Thread-safe method to update a manifest entry with reload"""
        with self._lock:
            try:
                # Reload to get latest changes from other threads
                self.reload_manifest()
                self.manifest[key] = value
                fileops.save_json(self.manifest_path, self.manifest)
            except Exception as e:
                logger.error(f"Failed to update manifest entry {key}: {e}")
    
    def get_manifest_entry(self, key, default=None):
        """Thread-safe method to get a manifest entry"""
        with self._lock:
            try:
                # Reload to get latest changes
                self.reload_manifest()
                return self.manifest.get(key, default)
            except Exception as e:
                logger.error(f"Failed to get manifest entry {key}: {e}")
                return default
    
    def needs_update(self, key, hash_val):
        with self._lock:
            try:
                self.reload_manifest()
                return self.manifest.get(key, {}).get('hash') != hash_val
            except Exception as e:
                logger.error(f"Failed to check update status for {key}: {e}")
                return True  # Assume update needed if we can't check
    
    def remove_old(self, pattern):
        for file in self.path.glob(pattern):
            if file.name != "manifest.json":
                file.unlink()

# === DATA MODELS ===
@dataclass
class Config:
    repo_url: str; content_goal: str; service_area: str
    support_materials: List[str] = field(default_factory=list); auto_confirm: bool = False
    work_dir: Path = field(default_factory=lambda: Path.cwd() / "work" / "tmp")
    max_repo_depth: int = 3; content_limit: int = 15000; phases: str = "1"
    debug_similarity: bool = False
    apply_changes: bool = False  # New field for Phase 3
    
    def __post_init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key: raise ValueError("OPENAI_API_KEY required")
        for dir_name in DIRS:
            fileops.mkdir(f"./llm_outputs/{dir_name}")

@dataclass
class ContentStrategy:
    thinking: str
    decisions: List[Dict]  # Changed from create_actions and update_actions
    confidence: float
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DocumentChunk:
    content: str; file_path: str; heading_path: List[str]; section_level: int; chunk_index: int
    frontmatter: Dict[str, Any]; embedding_content: str; embedding: Optional[List[float]] = None
    content_hash: Optional[str] = None; file_id: str = ""; chunk_id: str = ""
    prev_chunk_id: Optional[str] = None; next_chunk_id: Optional[str] = None
    parent_heading_chunk_id: Optional[str] = None; total_chunks_in_file: int = 0

@dataclass
class Result:
    working_directory: str; justification: str; confidence: float; repo_url: str; repo_path: str
    material_summaries: List[Dict]; content_goal: str; service_area: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    directory_ready: bool = False; working_directory_full_path: Optional[str] = None
    setup_error: Optional[str] = None; content_strategy: Optional[ContentStrategy] = None
    strategy_ready: bool = False
    # New fields for Phase 3
    generation_results: Optional[Dict] = None
    generation_ready: bool = False

# === BASE PROCESSOR ===
class SmartProcessor:
    def __init__(self, client, config): self.client, self.config = client, config
    def process(self, *args, **kwargs): return self._process(*args, **kwargs)
    def _process(self, *args, **kwargs): raise NotImplementedError
    
    def llm_call(self, system: str, user: str, model: str = "gpt-4o-mini") -> Dict:
        response = self.client.chat.completions.create(
            model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3, response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content)
    
    def save_interaction(self, prompt: str, response: Any, operation: str, output_dir: str, source: str = ""):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_source = re.sub(r'[^\w\s-]', '_', source)[:50] if source else operation
        base_path = Path(output_dir) / f"{timestamp}_{safe_source}"
        fileops.write(base_path.with_suffix('.txt'), f"=== {operation.upper()} ===\n{datetime.now().isoformat()}\n{'='*50}\n\n{prompt}")
        fileops.save_json(base_path.with_suffix('.json'), {"metadata": {"timestamp": datetime.now().isoformat(), "operation": operation}, "data": response})

# === CONTENT EXTRACTION ===
class ContentExtractor:
    def __init__(self, config): self.config = config
    
    @error_handler
    def extract(self, source: str, repo_path: Optional[Path] = None) -> Optional[str]:
        if source.startswith(('http://', 'https://')): return self._extract_url(source)
        return self._extract_file(source)
    
    def _extract_file(self, source: str) -> Optional[str]:
        path = Path(source)
        if not path.exists(): return None
        
        ext = path.suffix.lower()
        extractors = {
            '.docx': lambda p: self._extract_docx(p) if HAS_DOCX else None,
            '.doc': lambda p: self._extract_docx(p) if HAS_DOCX else None,
            '.pdf': lambda p: self._extract_pdf(p) if HAS_PDF else None,
        }
        
        return extractors.get(ext, lambda p: fileops.read(p, self.config.content_limit))(path)
    
    def _extract_docx(self, path):
        doc = Document(path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                parts.extend(c.text.strip() for c in row.cells if c.text.strip())
        return '\n'.join(parts)[:self.config.content_limit]
    
    def _extract_pdf(self, path):
        with open(path, 'rb') as f:
            reader = PdfReader(f)
            content = ""
            for page in reader.pages[:10]:
                if text := page.extract_text():
                    content += text + '\n'
                if len(content) > self.config.content_limit:
                    break
        return content[:self.config.content_limit]
    
    def _extract_url(self, source: str) -> Optional[str]:
        if not HAS_WEB: return None
        resp = requests.get(source, timeout=30, headers={'User-Agent': 'Mozilla/5.0 (DocBot/1.0)'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for s in soup(["script", "style"]): s.decompose()
        return '\n'.join(line.strip() for line in soup.get_text().splitlines() if line.strip())[:self.config.content_limit]

# === PROCESSORS ===
class MaterialProcessor(SmartProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = ContentExtractor(self.config)
    
    def _process(self, materials: List[str], repo_path: Path) -> List[Dict]:
        summaries = []
        for material in materials:
            if content := self.extractor.extract(material, repo_path):
                if summary := self._summarize(content, material):
                    summaries.append(summary)
        logger.info(f"Processed {len(summaries)}/{len(materials)} materials")
        return summaries
    
    def _summarize(self, content: str, source: str) -> Optional[Dict]:
        prompt = get_material_summary_prompt(source, content)
        system = MATERIAL_SUMMARY_SYSTEM
        try:
            result = self.llm_call(system, prompt)
            self.save_interaction(prompt, result, "materials_summary", "./llm_outputs/materials_summary", source)
            return result
        except Exception: return None

class DirectoryDetector(SmartProcessor):
    def _process(self, repo_path: Path, repo_structure: str, summaries: List[Dict]) -> Dict:
        materials_info = self._format_materials(summaries) if summaries else "No materials"
        prompt = get_directory_selection_prompt(self.config, str(repo_path), repo_structure, materials_info)
        system = DIRECTORY_SELECTION_SYSTEM
        result = self.llm_call(system, prompt, "gpt-4o")
        self.save_interaction(prompt, result, "working_directory", "./llm_outputs/decisions/working_directory")
        return result
    
    def _format_materials(self, summaries):
        return "\n".join([
            f"• {s.get('source', 'Unknown')}: {s.get('main_topic', 'N/A')}\n"
            f"  Summary: {s.get('summary', 'N/A')}\n"
            f"  Technologies: {', '.join(s.get('technologies', []) or [])}\n"
            f"  Key Concepts: {', '.join(s.get('key_concepts', []) or [])}\n"
            f"  Products: {', '.join(s.get('microsoft_products', []) or [])}"
            for s in summaries
        ])

# === CHUNKING SYSTEM ===
class SmartChunker:
    def __init__(self, max_size=3000, min_size=500):
        self.max_size, self.min_size = max_size, min_size
    
    def chunk_markdown(self, file_path: Path, cache: UnifiedCache) -> List[DocumentChunk]:
        content = fileops.read(file_path, limit=None)
        frontmatter, body = self._parse_frontmatter(content)
        
        chunks = []
        file_id = fileops.get_hash(file_path)
        self._process_body(body, file_path, frontmatter, file_id, chunks, cache)
        
        # Link chunks
        for i, chunk in enumerate(chunks):
            chunk.total_chunks_in_file = len(chunks)
            if i > 0:
                chunk.prev_chunk_id = chunks[i-1].chunk_id
                chunks[i-1].next_chunk_id = chunk.chunk_id
        
        return chunks
    
    def _parse_frontmatter(self, content: str) -> tuple:
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}, parts[2]
                except yaml.YAMLError:
                    pass
        return {}, content
    
    def _process_body(self, body: str, file_path: Path, frontmatter: Dict, file_id: str, chunks: List, cache: UnifiedCache):
        current_chunk = ""
        heading_stack = []
        heading_to_chunk_id = {}
        current_parent_id = None
        
        for line in body.split('\n'):
            if line.startswith('#'):
                if current_chunk.strip():
                    self._add_chunks(current_chunk.strip(), file_path, heading_stack[:], frontmatter,
                                   file_id, current_parent_id, chunks)
                
                level = len(line) - len(line.lstrip('#'))
                heading = line.lstrip('# ').strip()
                heading_stack = heading_stack[:level-1] + [heading]
                
                current_chunk_id = get_hash(f"{file_id}_{' > '.join(heading_stack)}")
                heading_to_chunk_id[' > '.join(heading_stack)] = current_chunk_id
                
                if level > 1 and len(heading_stack) > 1:
                    parent_heading = ' > '.join(heading_stack[:-1])
                    current_parent_id = heading_to_chunk_id.get(parent_heading)
                else:
                    current_parent_id = None
                
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk.strip():
            self._add_chunks(current_chunk.strip(), file_path, heading_stack, frontmatter,
                           file_id, current_parent_id, chunks)
    
    def _add_chunks(self, content: str, file_path: Path, heading_path: List[str], frontmatter: Dict,
                   file_id: str, parent_id: str, chunks: List):
        for chunk_content in self._smart_split(content):
            chunk_id = get_hash(f"{file_id}_{len(chunks)}_{chunk_content[:50]}")
            chunks.append(self._create_chunk(chunk_content, file_path, heading_path, frontmatter,
                                           len(chunks), file_id, chunk_id, parent_id))
    
    def _smart_split(self, content: str) -> List[str]:
        if len(content) <= self.max_size:
            return [content]
        
        chunks = []
        paragraphs = content.split('\n\n')
        current = ""
        
        for para in paragraphs:
            if len(current) + len(para) + 2 <= self.max_size:
                current += para + '\n\n'
            else:
                if len(current) >= self.min_size:
                    chunks.append(current.strip())
                    current = para + '\n\n'
                else:
                    current += para + '\n\n'
                    if len(current) >= self.min_size:
                        chunks.append(current.strip())
                        current = ""
        
        if current.strip():
            chunks.append(current.strip())
        
        return chunks or [content]
    
    def _create_chunk(self, content: str, file_path: Path, heading_path: List[str], frontmatter: Dict,
                     index: int, file_id: str, chunk_id: str, parent_id: str) -> DocumentChunk:
        # Build embedding content
        context_parts = []
        if frontmatter:
            if title := frontmatter.get('title'):
                context_parts.append(f"Document: {title}")
            if topic := frontmatter.get('ms.topic'):
                context_parts.append(f"Topic: {topic}")
            if desc := frontmatter.get('description'):
                context_parts.append(f"Description: {desc[:100]}")
        
        if heading_path:
            context_parts.append(f"Section: {' > '.join(heading_path)}")
        
        context_parts.append(content)
        embedding_content = " | ".join(filter(None, context_parts))
        
        # Don't cache here - just return the chunk
        return DocumentChunk(
            content=content.strip(),
            file_path=str(file_path),
            heading_path=heading_path,
            section_level=len(heading_path),
            chunk_index=index,
            frontmatter=frontmatter,
            embedding_content=embedding_content,
            embedding=None,  # No embedding yet
            content_hash=get_hash(embedding_content),
            file_id=file_id,
            chunk_id=chunk_id,
            parent_heading_chunk_id=parent_id
        )

# === CONTENT DISCOVERY ===
class ContentDiscoveryProcessor(SmartProcessor):
    def _process(self, working_dir_path: Path, repo_name: str, working_directory: str) -> List[DocumentChunk]:
        cache_dir = Path(f"./llm_outputs/embeddings/{repo_name}/{working_directory}")
        cache = UnifiedCache(cache_dir)
        chunker = SmartChunker()
        
        chunks = []
        md_files = list(working_dir_path.rglob("*.md"))
        regenerated = cached = 0
        
        logger.info(f"Processing {len(md_files)} markdown files in {working_directory}")
        
        # Process files
        files_to_process = []
        for md_file in md_files:
            file_hash = fileops.get_hash(md_file)
            if cache.needs_update(str(md_file), file_hash):
                # Clean up old chunks before reprocessing
                old_manifest_entry = cache.get_manifest_entry(str(md_file), {})
                old_chunk_ids = old_manifest_entry.get('chunk_ids', [])
                
                if old_chunk_ids:
                    removed_count = 0
                    for chunk_id in old_chunk_ids:
                        chunk_file = cache.path / f"{chunk_id}.json"
                        if chunk_file.exists():
                            try:
                                chunk_file.unlink()
                                removed_count += 1
                            except Exception as e:
                                logger.warning(f"Failed to remove chunk {chunk_id}: {e}")
                    
                    if removed_count > 0:
                        logger.info(f"Cleaned up {removed_count} orphaned chunks for {md_file.name}")
                
                files_to_process.append(md_file)
                logger.debug(f"File changed, will reprocess: {md_file.name}")
            else:
                # Load cached chunks
                manifest_entry = cache.get_manifest_entry(str(md_file), {})
                chunk_ids = manifest_entry.get('chunk_ids', [])
                chunks_loaded = 0
                for chunk_id in chunk_ids:
                    if cached_data := cache.get(chunk_id):
                        if 'meta' in cached_data:
                            chunk = self._reconstruct_chunk(md_file, cached_data)
                            chunks.append(chunk)
                            chunks_loaded += 1
                            # Check if embedding is loaded
                            if chunk.embedding:
                                logger.debug(f"Loaded chunk with embedding from cache: {chunk_id[:8]}...")
                            else:
                                logger.debug(f"Loaded chunk WITHOUT embedding from cache: {chunk_id[:8]}...")
                if chunks_loaded > 0:
                    logger.debug(f"Loaded {chunks_loaded} chunks from cache for {md_file.name}")
                cached += 1
        
        # Process new files in parallel
        if files_to_process:
            with ThreadPoolExecutor(max_workers=min(5, len(files_to_process))) as executor:
                futures = {executor.submit(self._process_file, md_file, chunker, cache): md_file 
                          for md_file in files_to_process}
                
                for future in as_completed(futures):
                    try:
                        file_chunks = future.result()
                        if file_chunks:
                            chunks.extend(file_chunks)
                            regenerated += 1
                    except Exception as e:
                        logger.error(f"Error processing {futures[future]}: {e}")
        
        logger.info(f"Discovered {len(chunks)} chunks. Files: {regenerated} regenerated, {cached} from cache")
        return chunks
    
    def _process_file(self, md_file: Path, chunker: SmartChunker, cache: UnifiedCache) -> List[DocumentChunk]:
        chunks = chunker.chunk_markdown(md_file, cache)
        
        # Store chunk metadata in cache for later embedding generation
        chunk_ids = []
        for chunk in chunks:
            chunk_meta = {
                'file_path': str(chunk.file_path),
                'heading_path': chunk.heading_path,
                'section_level': chunk.section_level,
                'chunk_index': chunk.chunk_index,
                'frontmatter': chunk.frontmatter,
                'embedding_content': chunk.embedding_content,
                'content_hash': chunk.content_hash,
                'file_id': chunk.file_id,
                'chunk_id': chunk.chunk_id,
                'parent_heading_chunk_id': chunk.parent_heading_chunk_id,
                'total_chunks_in_file': chunk.total_chunks_in_file,
                'prev_chunk_id': chunk.prev_chunk_id,
                'next_chunk_id': chunk.next_chunk_id
            }
            # Store metadata only (no embedding data yet)
            cache.put(chunk.chunk_id, None, chunk_meta)
            chunk_ids.append(chunk.chunk_id)
        
        # Update manifest with file info
        cache.update_manifest_entry(str(md_file), {
            'hash': fileops.get_hash(md_file),
            'chunk_ids': chunk_ids,
            'timestamp': datetime.now().isoformat()
        })
        return chunks
    
    def _reconstruct_chunk(self, md_file: Path, cached_data: Dict) -> DocumentChunk:
        meta = cached_data.get('meta', {})
        return DocumentChunk(
            content="",  # Content not needed for embeddings
            file_path=str(md_file),
            heading_path=meta.get('heading_path', []),
            section_level=meta.get('section_level', 0),
            chunk_index=meta.get('chunk_index', 0),
            frontmatter=meta.get('frontmatter', {}),
            embedding_content=meta.get('embedding_content', ""),
            embedding=cached_data.get('data'),  # This is the actual embedding
            content_hash=meta.get('content_hash'),
            file_id=meta.get('file_id', ""),
            chunk_id=meta.get('chunk_id', ""),
            parent_heading_chunk_id=meta.get('parent_heading_chunk_id'),
            total_chunks_in_file=meta.get('total_chunks_in_file', 0),
            prev_chunk_id=meta.get('prev_chunk_id'),
            next_chunk_id=meta.get('next_chunk_id')
        )

# === STRATEGY PROCESSOR ===
class ContentStrategyProcessor(SmartProcessor):
    def _process(self, chunks: List[DocumentChunk], materials: List[Dict], config: Config, repo_name: str, working_directory: str) -> ContentStrategy:
        cache_dir = Path(f"./llm_outputs/embeddings/{repo_name}/{working_directory}")
        intent_embedding = self._create_intent_embedding(config, materials, cache_dir)
        similar_chunks = self._find_similar_content(intent_embedding, chunks, cache_dir)[:10]
        strategy = self._generate_strategy(config, materials, similar_chunks)
        
        # Content types are now handled within the unified prompt
        return strategy
    
    def _load_content_standards(self) -> Dict:
        """Load content standards from JSON file"""
        standards_path = Path("content_standards.json")
        if standards_path.exists():
            return fileops.load_json(standards_path)
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
    
    def _determine_content_type(self, config: Config, filename: str, reason: str, materials: List[Dict]) -> Dict:
        """Use LLM to determine appropriate content type for new content"""
        standards = self._load_content_standards()
        content_types = standards.get('contentTypes', [])
        
        materials_summary = "\n".join([
            f"• {m.get('main_topic', 'Unknown')}: {m.get('summary', 'N/A')[:100]}"
            for m in materials[:3]
        ])
        
        prompt = get_unified_content_strategy_prompt(
            config.content_goal,
            filename,
            reason,
            materials_summary,
            content_types
        )
        
        try:
            result = self.llm_call(UNIFIED_CONTENT_STRATEGY_SYSTEM, prompt, "gpt-4o")
            self.save_interaction(prompt, result, "content_type_selection", 
                                "./llm_outputs/content_strategy", filename)
            return {
                'content_type': result.get('content_type', 'How-To Guide'),
                'ms_topic': result.get('ms_topic', 'how-to'),
                'justification': result.get('justification', ''),
                'confidence': result.get('confidence', 0.5)
            }
        except Exception as e:
            logger.error(f"Content type selection failed: {e}")
            return {
                'content_type': 'How-To Guide',
                'ms_topic': 'how-to',
                'justification': 'Default selection due to error',
                'confidence': 0.0
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
                content = fileops.read(full_path, limit=2000)  # Only need frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        return frontmatter.get('ms.topic')
        except Exception as e:
            logger.warning(f"Could not extract ms.topic from {file_path}: {e}")
        
        return None
    
    def _enhance_with_content_types(self, strategy: ContentStrategy, config: Config, 
                                   materials: List[Dict], chunks: List[DocumentChunk]) -> ContentStrategy:
        """Enhance strategy actions with content type information"""
        
        # Enhance CREATE actions
        enhanced_create_actions = []
        for action in strategy.decisions:
            enhanced_action = action.copy()
            
            # Determine content type for new content
            content_type_info = self._determine_content_type(
                config,
                action.get('filename', 'new-content.md'),
                action.get('reason', ''),
                materials
            )
            
            enhanced_action['content_type'] = content_type_info['content_type']
            enhanced_action['ms_topic'] = content_type_info['ms_topic']
            enhanced_action['content_type_justification'] = content_type_info['justification']
            enhanced_create_actions.append(enhanced_action)
            
            logger.info(f"CREATE action '{action.get('filename')}' assigned content type: {content_type_info['content_type']}")
        
        # Enhance UPDATE actions
        enhanced_update_actions = []
        for action in strategy.decisions:
            enhanced_action = action.copy()
            
            # Extract ms.topic from existing file
            filename = action.get('filename', '')
            ms_topic = self._extract_ms_topic(filename, chunks)
            
            if ms_topic:
                enhanced_action['ms_topic'] = ms_topic
                # Map ms.topic to content type name
                standards = self._load_content_standards()
                for ct in standards.get('contentTypes', []):
                    if ct['frontMatter'].get('ms.topic') == ms_topic:
                        enhanced_action['content_type'] = ct['name']
                        break
                else:
                    enhanced_action['content_type'] = 'Unknown'
                
                logger.info(f"UPDATE action '{filename}' identified as content type: {enhanced_action.get('content_type')} (ms.topic: {ms_topic})")
            else:
                enhanced_action['ms_topic'] = 'unknown'
                enhanced_action['content_type'] = 'Unknown'
                logger.warning(f"Could not determine content type for '{filename}'")
            
            enhanced_update_actions.append(enhanced_action)
        
        # Create enhanced strategy
        return ContentStrategy(
            thinking=strategy.thinking + f"\n\nContent types determined: {len(enhanced_create_actions)} CREATE actions assigned types, {len(enhanced_update_actions)} UPDATE actions identified.",
            decisions=enhanced_create_actions + enhanced_update_actions,
            confidence=strategy.confidence,
            summary=strategy.summary + " (with content types)"
        )
    
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
        file_stats = []
        for file_id, file_chunks in chunks_by_file.items():
            if file_chunks:  # Only process files with chunks
                file_path = file_chunks[0].chunk.file_path
                file_name = Path(file_path).name
                avg_score = sum(d.score for d in file_chunks) / len(file_chunks)
                
                # Determine relevance level
                if avg_score > 0.7: relevance = "HIGH ⬆️"
                elif avg_score > 0.5: relevance = "MEDIUM ↗️"
                elif avg_score > 0.3: relevance = "LOW →"
                else: relevance = "MINIMAL ↘️"
                
                file_stats.append((file_name, len(file_chunks), avg_score, relevance))
        
        # Sort by average score
        file_stats.sort(key=lambda x: x[2], reverse=True)
        
        # Print table
        print(f"\n{'File':<35} | {'Chunks':>7} | {'Avg Score':>9} | {'Relevance':<12}")
        print(f"{'-'*35}-+-{'-'*7}-+-{'-'*9}-+-{'-'*12}")
        
        for file_name, chunk_count, avg_score, relevance in file_stats[:10]:
            print(f"{file_name[:33]:<35} | {chunk_count:>7} | {avg_score:>9.3f} | {relevance:<12}")
    
    def _print_boost_details(self, chunk_data: Dict, file_relevance: Dict, boosted_scores: Dict, limit: int = 10):
        """Print detailed boost calculations"""
        self._print_debug_header("BOOST CALCULATIONS (Top 10)")
        
        # Get top chunks by boosted score
        top_chunks = sorted(boosted_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        for i, (chunk_id, final_score) in enumerate(top_chunks, 1):
            data = chunk_data[chunk_id]
            chunk = data.chunk
            base_score = data.score
            
            print(f"\nChunk #{i}: {Path(chunk.file_path).name} > {' > '.join(chunk.heading_path)}")
            print(f"├─ Base Score: {base_score:.3f}")
            
            # File boost
            file_avg = file_relevance.get(chunk.file_id, 0)
            file_boost = 0.1 * file_avg if file_avg > 0.5 else 0
            if file_boost > 0:
                print(f"├─ File Boost: +{file_boost:.3f} (file avg: {file_avg:.3f} > 0.5 threshold)")
            
            # Proximity boosts
            proximity_boost = 0
            print(f"├─ Proximity Boosts:")
            
            if chunk.prev_chunk_id and chunk.prev_chunk_id in chunk_data:
                prev_score = chunk_data[chunk.prev_chunk_id].score
                if prev_score > 0.6:
                    print(f"│  ├─ Previous chunk: {prev_score:.3f} > 0.6 → +0.05")
                    proximity_boost += 0.05
            
            if chunk.next_chunk_id and chunk.next_chunk_id in chunk_data:
                next_score = chunk_data[chunk.next_chunk_id].score
                if next_score > 0.6:
                    print(f"│  └─ Next chunk: {next_score:.3f} > 0.6 → +0.05")
                    proximity_boost += 0.05
            
            # Parent boost
            if chunk.parent_heading_chunk_id and chunk.parent_heading_chunk_id in chunk_data:
                parent_score = chunk_data[chunk.parent_heading_chunk_id].score
                if parent_score > 0.7:
                    print(f"├─ Parent Boost: +0.03 (parent: {parent_score:.3f} > 0.7)")
            
            print(f"└─ FINAL SCORE: {final_score:.3f} {'⭐' if i == 1 else ''}")
    
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
        high_relevance = [(cid, score) for cid, score in boosted_scores.items() if score > 0.8]
        medium_relevance = [(cid, score) for cid, score in boosted_scores.items() if 0.5 < score <= 0.8]
        low_relevance = [(cid, score) for cid, score in boosted_scores.items() if score <= 0.5]
        
        print(f"\nHIGH RELEVANCE (0.8+): {len(high_relevance)} chunks")
        if high_relevance:
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
        
        print(f"\nMEDIUM RELEVANCE (0.5-0.8): {len(medium_relevance)} chunks")
        if medium_relevance:
            print(f"→ Topics partially covered: Related content exists")
            print(f"→ Strategy: ENHANCE with new specific details from materials")
            print(f"→ Intent alignment: Some overlap but missing key aspects")
        
        print(f"\nLOW RELEVANCE (<0.5): {len(low_relevance)} chunks")
        print(f"→ Gap identified: Content not well covered")
        print(f"→ Strategy: CREATE new dedicated documentation")
        print(f"→ Intent alignment: Materials cover topics not in existing content")
        
        print(f"\nRECOMMENDED ACTIONS:")
        print(f"Based on similarity distribution, expect:")
        print(f"- CREATE actions for gaps (low similarity areas)")
        print(f"- UPDATE actions for high similarity areas needing enhancement")
        
        # Show distribution
        total_chunks = len(boosted_scores)
        if total_chunks > 0:
            print(f"\nSCORE DISTRIBUTION:")
            print(f"├─ High (0.8+):   {len(high_relevance):>3} chunks ({len(high_relevance)/total_chunks*100:>5.1f}%)")
            print(f"├─ Medium (0.5-0.8): {len(medium_relevance):>3} chunks ({len(medium_relevance)/total_chunks*100:>5.1f}%)")
            print(f"└─ Low (<0.5):    {len(low_relevance):>3} chunks ({len(low_relevance)/total_chunks*100:>5.1f}%)")
            
            # Provide interpretation
            print(f"\nINTERPRETATION:")
            if len(high_relevance) / total_chunks > 0.3:
                print("→ Strong existing coverage - expect mostly UPDATE actions")
            elif len(low_relevance) / total_chunks > 0.7:
                print("→ Significant content gaps - expect mostly CREATE actions")
            else:
                print("→ Mixed coverage - expect both CREATE and UPDATE actions")
    
    def _create_intent_embedding(self, config: Config, materials: List[Dict], cache_dir: Path) -> List[float]:
        # Build intent text
        intent_parts = [f"Goal: {config.content_goal}", f"Service: {config.service_area}"]
        
        for key, label in [('main_topic', 'Topics'), ('technologies', 'Technologies'), 
                          ('key_concepts', 'Key concepts'), ('document_type', 'Content types')]:
            values = [m.get(key) for m in materials if m.get(key)]
            if key in ['technologies', 'key_concepts']:
                values = [v for m in materials for v in m.get(key, [])]
            if values:
                intent_parts.append(f"{label}: {', '.join(values[:10])}")
        
        intent_text = " | ".join(intent_parts)
        
        # Log the full intent for debugging
        if config.debug_similarity:
            self._print_debug_header("INTENT EMBEDDING CONSTRUCTION")
            print(f"\nFull Intent Text ({len(intent_text)} chars):")
            print("-" * 60)
            print(intent_text)
            print("-" * 60)
            print(f"\nExtracted Components:")
            print(f"- Topics: {len([m.get('main_topic', '') for m in materials if m.get('main_topic')])}")
            print(f"- Technologies: {len([t for m in materials for t in m.get('technologies', [])])}")
            print(f"- Concepts: {len([c for m in materials for c in m.get('key_concepts', [])])}")
            print(f"- Document Types: {len(set(m.get('document_type', '') for m in materials if m.get('document_type')))}")
        
        # Check cache
        cache = UnifiedCache(cache_dir)
        cache_key = get_hash(intent_text)
        if cached := cache.get(cache_key):
            logger.info("Using cached intent embedding")
            return cached['data']
        
        # Generate new
        try:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=intent_text)
            embedding = response.data[0].embedding
            cache.put(cache_key, embedding, {'type': 'intent', 'text': intent_text[:100]})
            logger.info("Created and cached new intent embedding")
            return embedding
        except:
            return []
    
    def _find_similar_content(self, intent_embedding: List[float], chunks: List[DocumentChunk], cache_dir: Path) -> List[DocumentChunk]:
        if not intent_embedding:
            return chunks[:10]
        
        cache = UnifiedCache(cache_dir)
        ChunkData = namedtuple('ChunkData', ['chunk', 'score'])
        chunk_data = {}
        
        # Track cache performance
        embeddings_from_cache = 0
        embeddings_generated = 0
        embeddings_already_loaded = 0
        
        # Generate embeddings
        for chunk in chunks:
            # Check if we have a valid embedding (not None and not empty)
            if not chunk.embedding:
                # Try to get from cache - reload to get latest data
                cached_entry = cache.get(chunk.chunk_id)
                if cached_entry and cached_entry.get('data') is not None:
                    # Data exists and is not None
                    chunk.embedding = cached_entry['data']
                    embeddings_from_cache += 1
                    logger.debug(f"Loaded embedding from cache for chunk {chunk.chunk_id}")
                else:
                    # Generate new embedding
                    try:
                        response = self.client.embeddings.create(
                            model="text-embedding-3-small",
                            input=chunk.embedding_content[:8000]
                        )
                        chunk.embedding = response.data[0].embedding
                        embeddings_generated += 1
                        
                        # Update cache with the actual embedding
                        # Get existing metadata
                        existing_meta = {}
                        if cached_entry:
                            existing_meta = cached_entry.get('meta', {})
                        
                        # Merge with updated metadata
                        updated_meta = {
                            **existing_meta,
                            'type': 'content',
                            'file': chunk.file_path,
                            'heading_path': chunk.heading_path,
                            'embedding_content': chunk.embedding_content,
                            'has_embedding': True
                        }
                        
                        # Save embedding to cache
                        cache.put(chunk.chunk_id, chunk.embedding, updated_meta)
                        logger.debug(f"Generated and cached new embedding for chunk {chunk.chunk_id}")
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for chunk {chunk.chunk_id}: {e}")
                        chunk.embedding = []
            else:
                embeddings_already_loaded += 1
            
            if chunk.embedding:
                score = self._cosine_similarity(intent_embedding, chunk.embedding)
                chunk_data[chunk.chunk_id] = ChunkData(chunk, score)
        
        # Log cache performance
        total_chunks = len(chunks)
        logger.info(f"Embedding cache performance: {embeddings_already_loaded} already loaded, "
                   f"{embeddings_from_cache} loaded from cache, {embeddings_generated} generated "
                   f"(total: {total_chunks} chunks)")
        
        # Print base scores if debug mode
        if self.config.debug_similarity and chunk_data:
            self._print_base_scores(chunk_data)
        
        # Apply boosts
        boosted_scores = self._apply_boosts(chunk_data)
        
        # Print debug info if enabled
        if self.config.debug_similarity and boosted_scores:
            # Group chunks by file
            chunks_by_file = defaultdict(list)
            for data in chunk_data.values():
                chunks_by_file[data.chunk.file_id].append(data)
            
            # Calculate file relevance
            file_relevance = {fid: sum(d.score for d in chunks)/len(chunks) 
                            for fid, chunks in chunks_by_file.items()}
            
            self._print_file_analysis(chunks_by_file)
            self._print_boost_details(chunk_data, file_relevance, boosted_scores)
            self._print_score_transformation(chunk_data, boosted_scores)
            self._print_strategy_insights(boosted_scores, chunk_data)
        
        # Sort and return
        sorted_chunks = sorted(boosted_scores.items(), key=lambda x: x[1], reverse=True)
        return [chunk_data[chunk_id].chunk for chunk_id, _ in sorted_chunks]
    
    def _cosine_similarity(self, a, b):
        return sum(x*y for x,y in zip(a,b)) / ((sum(x*x for x in a) * sum(y*y for y in b))**0.5) if a and b else 0
    
    def _apply_boosts(self, chunk_scores: Dict) -> Dict:
        # Calculate file relevance
        file_scores = defaultdict(list)
        for chunk_id, (chunk, score) in chunk_scores.items():
            file_scores[chunk.file_id].append(score)
        
        file_relevance = {fid: sum(scores)/len(scores) for fid, scores in file_scores.items()}
        
        # Apply boosts
        boosted = {}
        for chunk_id, (chunk, score) in chunk_scores.items():
            boost = 0
            
            # File context boost
            if file_relevance.get(chunk.file_id, 0) > 0.5:
                boost += 0.1 * file_relevance[chunk.file_id]
            
            # Proximity boosts
            if chunk.prev_chunk_id in chunk_scores and chunk_scores[chunk.prev_chunk_id][1] > 0.6:
                boost += 0.05
            if chunk.next_chunk_id in chunk_scores and chunk_scores[chunk.next_chunk_id][1] > 0.6:
                boost += 0.05
            
            # Parent section boost
            if chunk.parent_heading_chunk_id in chunk_scores and chunk_scores[chunk.parent_heading_chunk_id][1] > 0.7:
                boost += 0.03
            
            boosted[chunk_id] = score + boost
        
        return boosted
    
    def _generate_strategy(self, config: Config, materials: List[Dict], similar_chunks: List[DocumentChunk]) -> ContentStrategy:
        materials_summary = "\n".join([
            f"• {m.get('main_topic', 'Unknown')}: {m.get('summary', 'N/A')[:200]}"
            for m in materials
        ])
        
        # Prepare semantic matches for the prompt
        semantic_matches = self._prepare_semantic_matches(similar_chunks)
        
        # Load content standards
        content_standards = self._load_content_standards()
        
        prompt = get_unified_content_strategy_prompt(config, materials_summary, semantic_matches, content_standards)
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
    
    def _prepare_semantic_matches(self, similar_chunks: List[DocumentChunk]) -> List[Dict]:
        """Prepare semantic matches in the format expected by the unified prompt"""
        # Group chunks by file with their similarity scores
        chunks_by_file = defaultdict(list)
        chunk_scores = {}  # Store similarity scores for chunks
        
        # For simplicity, assume chunks are ordered by similarity (best first)
        # Assign descending scores based on position
        for idx, chunk in enumerate(similar_chunks[:50]):
            # Simulate scores based on position (first chunk = highest score)
            score = 0.9 - (idx * 0.01)  # Scores from 0.9 down
            chunk_scores[chunk.chunk_id] = score
            chunks_by_file[chunk.file_path].append((chunk, score))
        
        # Create file-level semantic matches
        semantic_matches = []
        for file_path, file_chunks_with_scores in chunks_by_file.items():
            # Extract chunks and scores
            file_chunks = [chunk for chunk, _ in file_chunks_with_scores]
            scores = [score for _, score in file_chunks_with_scores]
            
            # Extract ms.topic from frontmatter
            ms_topic = 'unknown'
            content_type = 'Unknown'
            if file_chunks[0].frontmatter:
                ms_topic = file_chunks[0].frontmatter.get('ms.topic', 'unknown')
                # Map ms.topic to content type
                content_type = self._map_ms_topic_to_content_type(ms_topic)
            
            # Calculate file relevance score (average of chunk scores)
            relevance_score = sum(scores) / len(scores) if scores else 0.0
            
            # Determine coverage level
            if relevance_score > 0.7:
                coverage_analysis = "High coverage - existing content addresses most concepts"
            elif relevance_score > 0.4:
                coverage_analysis = "Medium coverage - partial coverage, missing important details"
            else:
                coverage_analysis = "Low coverage - minimal relevant content"
            
            # Extract matched sections
            matched_sections = []
            for chunk in file_chunks[:5]:
                if chunk.heading_path:
                    matched_sections.append(' > '.join(chunk.heading_path))
            
            semantic_matches.append({
                'file': Path(file_path).name,
                'content_type': content_type,
                'ms_topic': ms_topic,
                'relevance_score': relevance_score,
                'coverage_analysis': coverage_analysis,
                'matched_sections': matched_sections
            })
        
        # Sort by relevance score
        semantic_matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        return semantic_matches[:10]  # Return top 10 files
    
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

# === REPOSITORY MANAGER ===
class RepositoryManager:
    extract_name = lambda self, url: urlparse(url.rstrip('.git')).path.rstrip('/').split('/')[-1] or "repo"
    
    def clone_or_update(self, repo_url: str, work_dir: Path) -> Path:
        fileops.mkdir(work_dir)
        repo_path = work_dir / self.extract_name(repo_url)
        if repo_path.exists() and (repo_path / '.git').exists():
            return self._update_repo(repo_path, repo_url)
        if repo_path.exists():
            shutil.rmtree(repo_path)
        return self._clone_repo(repo_url, repo_path)
    
    def _run_git(self, cmd: List[str], cwd: Path = None):
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    
    def _update_repo(self, repo_path: Path, repo_url: str) -> Path:
        logger.info(f"Updating: {repo_path}")
        try:
            self._run_git(["git", "fetch", "--all"], repo_path)
            self._run_git(["git", "reset", "--hard", "origin/HEAD"], repo_path)
            logger.info("Updated successfully")
            return repo_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"Update failed: {e.stderr}. Fresh clone...")
            shutil.rmtree(repo_path)
            return self._clone_repo(repo_url, repo_path)
    
    def _clone_repo(self, repo_url: str, repo_path: Path) -> Path:
        logger.info(f"Cloning {repo_url}")
        self._run_git(["git", "clone", "--depth", "1", repo_url, str(repo_path)])
        logger.info("Cloned successfully")
        return repo_path
    
    def get_structure(self, repo_path: Path, max_depth: int = 3) -> str:
        lines = []
        
        def add_dir(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth: return
            try:
                items = sorted([item for item in path.iterdir() if not item.name.startswith('.')], 
                             key=lambda x: (not x.is_dir(), x.name))
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    curr = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{curr}{item.name}/")
                        add_dir(item, prefix + next_prefix, depth + 1)
                    elif item.suffix in ['.md', '.yml', '.yaml'] or item.name == 'TOC.yml':
                        lines.append(f"{prefix}{curr}{item.name}")
            except PermissionError:
                pass
        
        add_dir(repo_path)
        return "\n".join(lines)

# === INTERACTIVE SYSTEM ===
class GenericInteractive:
    def __init__(self, config, formatter=None):
        self.config = config
        self.formatter = formatter or (lambda x: str(x))
    
    def confirm(self, result, failed=False, error=""):
        if failed:
            return self._handle_failure(error)
        if self.config.auto_confirm:
            logger.info(f"Auto-confirming: {self._get_summary(result)}")
            return result
        return self._interact(result)
    
    def _get_summary(self, result):
        if isinstance(result, dict):
            return result.get('working_directory', result.get('summary', str(result)))
        return getattr(result, 'summary', str(result))
    
    def _handle_failure(self, error):
        print(f"\n{'='*80}\n⚠️  FAILED - MANUAL REQUIRED\n{'='*80}\n🚫 Error: {error}\n{'='*80}")
        return self._manual_selection(f"Manual fallback: {error}")
    
    def _interact(self, result):
        self.formatter(result)
        while True:
            choice = input("\n1) Accept | 2) Browse | 3) Search | Choice: ").strip()
            if choice == '1':
                return result
            elif choice in ['2', '3']:
                return self._manual_selection("User override")
    
    def _manual_selection(self, reason):
        # Override in subclasses
        return None

class DirectoryConfirmation(GenericInteractive):
    def __init__(self, config):
        super().__init__(config, self._format_directory)
        self.repo_structure = None
    
    def confirm(self, llm_result: Optional[Dict], repo_structure: str, llm_failed: bool = False, error: str = "") -> Dict:
        self.repo_structure = repo_structure
        return super().confirm(llm_result, llm_failed, error)
    
    def _format_directory(self, result):
        print(f"\n{'='*80}\n📁 WORKING DIRECTORY RECOMMENDATION\n{'='*80}")
        print(f"🤖 Suggested: {result['working_directory']} (Confidence: {result['confidence']:.1%})")
        print(f"📝 Reason: {result['justification']}\n{'='*80}")
    
    def _manual_selection(self, reason):
        directories = self._extract_directories(self.repo_structure)
        selector = InteractiveSelector()
        
        while True:
            choice = input("\n1) Browse | 2) Search | Choice: ").strip()
            if choice == '1':
                if selected := selector.paginated_selection(directories, "Browse Directories"):
                    return {'working_directory': selected, 'justification': reason, 'confidence': 1.0}
            elif choice == '2':
                if selected := selector.search_and_select(directories, "Search Directories"):
                    return {'working_directory': selected, 'justification': reason, 'confidence': 1.0}
    
    def _extract_directories(self, structure: str) -> List[str]:
        dirs, path = [], []
        for line in structure.split('\n'):
            if not line.strip() or not line.lstrip().endswith('/'):
                continue
            clean = line.replace('├── ', '').replace('└── ', '').replace('│   ', '    ')
            depth = (len(clean) - len(clean.lstrip())) // 4
            name = clean.strip().rstrip('/')
            path = path[:depth] + [name]
            dirs.append('/'.join(path))
        return sorted(set(dirs))

class StrategyConfirmation(GenericInteractive):
    def __init__(self, config):
        super().__init__(config, self._format_strategy)
    
    def _format_strategy(self, strategy):
        print(f"\n{'='*80}\n📋 CONTENT STRATEGY RECOMMENDATION\n{'='*80}")
        print(f"🤖 Strategy: {strategy.summary} (Confidence: {strategy.confidence:.1%})")
        print(f"📝 Analysis: {strategy.thinking[:200]}...\n{'='*80}")
        self._display_actions(strategy)
    
    def _display_actions(self, strategy):
        if not strategy.decisions:
            print("\nNo actions recommended.")
            return
            
        create_actions = [d for d in strategy.decisions if d.get('action') == 'CREATE']
        update_actions = [d for d in strategy.decisions if d.get('action') == 'UPDATE']
        
        if create_actions:
            print(f"\nCREATE Actions ({len(create_actions)}):")
            for i, action in enumerate(create_actions[:3], 1):
                filename = action.get('filename', 'new-content.md')
                reason = action.get('reason', 'No reason provided')[:60]
                content_type = action.get('content_type', 'Unknown')
                ms_topic = action.get('ms_topic', 'unknown')
                priority = action.get('priority', 'medium')
                print(f"  {i}. {filename} - {reason}...")
                print(f"     Content Type: {content_type} (ms.topic: {ms_topic}) | Priority: {priority}")
                if action.get('relevant_chunks'):
                    print(f"     Reference chunks: {len(action['relevant_chunks'])} available")
        
        if update_actions:
            print(f"\nUPDATE Actions ({len(update_actions)}):")
            for i, action in enumerate(update_actions[:3], 1):
                filename = action.get('filename', 'existing.md')
                change_desc = action.get('change_description', 'Update content')[:60]
                current_type = action.get('current_content_type', 'Unknown')
                priority = action.get('priority', 'medium')
                print(f"  {i}. {filename} - {change_desc}...")
                print(f"     Current Type: {current_type} | Priority: {priority}")
                if action.get('specific_sections'):
                    print(f"     Sections to add: {', '.join(action['specific_sections'][:3])}")
                if action.get('relevant_chunks'):
                    print(f"     Reference chunks: {len(action['relevant_chunks'])} available")
    
    def _manual_selection(self, reason):
        return ContentStrategy("User override", [], 0.0, reason)

class InteractiveSelector:
    @staticmethod
    def paginated_selection(items: List[str], title: str = "Select Item", page_size: int = 25) -> Optional[str]:
        if not items: return None
        
        current_page = 1
        total_pages = (len(items) + page_size - 1) // page_size
        
        while True:
            start = (current_page - 1) * page_size
            end = min(current_page * page_size, len(items))
            
            print(f"\n{'='*80}\n📁 {title} (Page {current_page}/{total_pages}) - {start+1}-{end} of {len(items)}\n{'='*80}")
            
            for i, item in enumerate(items[start:end], start+1):
                print(f"{i:3d}. {item}")
            
            print(f"\n{'-'*60}\nOptions: 1-{len(items)}) Select", end="")
            if current_page > 1: print(" | p) Previous", end="")
            if current_page < total_pages: print(" | n) Next", end="")
            if total_pages > 1: print(" | g) Go to page", end="")
            print(" | q) Quit\n" + "-"*60)
            
            try:
                choice = input("Choice: ").strip().lower()
                if choice.isdigit() and 1 <= int(choice) <= len(items):
                    selected = items[int(choice) - 1]
                    print(f"✅ Selected: {selected}")
                    return selected
                elif choice == 'p' and current_page > 1:
                    current_page -= 1
                elif choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif choice == 'g' and total_pages > 1:
                    try:
                        current_page = max(1, min(total_pages, int(input(f"Page (1-{total_pages}): "))))
                    except ValueError:
                        print("Invalid page")
                elif choice == 'q':
                    return None
                else:
                    print("Invalid choice")
            except (KeyboardInterrupt, EOFError):
                return None
    
    @staticmethod
    def search_and_select(items: List[str], title: str = "Search") -> Optional[str]:
        term = input("Search term: ").strip()
        if not term: return None
        
        filtered = [item for item in items if term.lower() in item.lower()]
        if not filtered:
            print(f"No matches for '{term}'")
            return None
        
        print(f"Found {len(filtered)} matches for '{term}'")
        return InteractiveSelector.paginated_selection(filtered, f"{title} - '{term}'")

# === ORCHESTRATOR ===
class ContentDeveloperOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.api_key) if HAS_OPENAI else None
        self.repo_manager = RepositoryManager()
        self.dir_confirmator = DirectoryConfirmation(config)
        self.strategy_confirmator = StrategyConfirmation(config)
    
    def execute(self) -> Result:
        logger.info(f"=== Content Developer: Phase(s) 1-{self.config.phases} ===")
        
        # Convert phases string to integer for comparison
        max_phase = int(self.config.phases) if self.config.phases.isdigit() else 1
        
        # Phase 1 - Always run if any phase is requested
        repo_path = self.repo_manager.clone_or_update(self.config.repo_url, self.config.work_dir)
        materials = MaterialProcessor(self.client, self.config).process(self.config.support_materials, repo_path)
        structure = self.repo_manager.get_structure(repo_path, self.config.max_repo_depth)
        
        llm_result, llm_failed, error = None, False, ""
        try:
            llm_result = DirectoryDetector(self.client, self.config).process(repo_path, structure, materials)
        except Exception as e:
            llm_failed, error = True, str(e)
            logger.warning(f"LLM failed: {error}")
        
        if self.config.auto_confirm and llm_failed:
            raise RuntimeError(f"Auto-confirm enabled but LLM failed: {error}")
        
        confirmed = self.dir_confirmator.confirm(llm_result, structure, llm_failed, error)
        setup_result = self._setup_directory(repo_path, confirmed['working_directory'])
        
        # Create result
        result = Result(
            working_directory=confirmed['working_directory'],
            justification=confirmed['justification'],
            confidence=confirmed['confidence'],
            repo_url=self.config.repo_url,
            repo_path=str(repo_path),
            material_summaries=materials,
            content_goal=self.config.content_goal,
            service_area=self.config.service_area,
            directory_ready=setup_result['success'],
            working_directory_full_path=setup_result.get('full_path'),
            setup_error=setup_result.get('error')
        )
        
        # Phase 2 - Run if phase 2 or higher is requested
        if max_phase >= 2 and result.directory_ready:
            try:
                logger.info("=== Phase 2: Content Strategy Analysis ===")
                working_dir_path = Path(setup_result['full_path'])
                chunks = ContentDiscoveryProcessor(self.client, self.config).process(
                    working_dir_path,
                    self.repo_manager.extract_name(self.config.repo_url),
                    confirmed['working_directory']
                )
                strategy = ContentStrategyProcessor(self.client, self.config).process(
                    chunks, materials, self.config,
                    self.repo_manager.extract_name(self.config.repo_url),
                    confirmed['working_directory']
                )
                confirmed_strategy = self.strategy_confirmator.confirm(strategy)
                result.content_strategy = confirmed_strategy
                result.strategy_ready = confirmed_strategy.confidence > 0
                logger.info(f"Phase 2 completed: {confirmed_strategy.summary}")
            except Exception as e:
                logger.error(f"Phase 2 failed: {e}")
                error_strategy = self.strategy_confirmator.confirm(None, True, str(e))
                result.content_strategy = error_strategy
                result.strategy_ready = False
        
        # Phase 3 - Run if phase 3 is requested
        if max_phase >= 3:
            if not result.strategy_ready:
                logger.error("Phase 3 requires completed Phase 2 strategy")
                return result
            
            try:
                logger.info("=== Phase 3: Content Generation ===")
                working_dir_path = Path(setup_result['full_path'])
                
                # Use ContentGenerator following same pattern as Phase 2
                generator = ContentGenerator(self.client, self.config)
                generation_results = generator.process(
                    result.content_strategy,
                    result.material_summaries,
                    working_dir_path,
                    self.repo_manager.extract_name(self.config.repo_url),
                    confirmed['working_directory']
                )
                
                # Store results in Result dataclass
                result.generation_results = generation_results
                result.generation_ready = True
                
                # Apply to repository if requested
                if self.config.apply_changes:
                    self._apply_generated_content(generation_results, working_dir_path)
                
                # Count successful results
                create_count = sum(1 for r in generation_results.get('create_results', []) if r.get('success'))
                update_count = sum(1 for r in generation_results.get('update_results', []) if r.get('success'))
                
                logger.info(f"Phase 3 completed: Generated {create_count} new files, "
                          f"updated {update_count} files")
                
            except Exception as e:
                logger.error(f"Phase 3 failed: {e}")
                result.generation_results = None
                result.generation_ready = False
        
        return result
    
    def _apply_generated_content(self, generation_results: Dict, working_dir_path: Path):
        """Apply generated content to the repository"""
        logger.info("Applying generated content to repository...")
        
        # Apply CREATE actions
        for result in generation_results.get('create_results', []):
            if result.get('success') and result.get('content'):
                file_path = working_dir_path / result['action']['filename']
                try:
                    fileops.write(file_path, result['content'])
                    logger.info(f"Created: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to create {file_path}: {e}")
        
        # Apply UPDATE actions
        for result in generation_results.get('update_results', []):
            if result.get('success') and result.get('updated_content'):
                file_path = working_dir_path / result['action']['filename']
                try:
                    fileops.write(file_path, result['updated_content'])
                    logger.info(f"Updated: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to update {file_path}: {e}")
    
    def _setup_directory(self, repo_path: Path, working_dir: str) -> Dict:
        if not working_dir:
            return {'success': False, 'error': 'No directory specified'}
        try:
            full_path = repo_path / working_dir
            if not full_path.exists():
                return {'success': False, 'error': f'Directory does not exist: {working_dir}'}
            if not full_path.is_dir():
                return {'success': False, 'error': f'Path is not a directory: {working_dir}'}
            logger.info(f"Working directory verified: {working_dir}")
            return {'success': True, 'full_path': str(full_path)}
        except Exception as e:
            logger.error(f"Directory verification failed: {e}")
            return {'success': False, 'error': str(e)}

# === DISPLAY ===
def display_results(result: Result):
    if HAS_RICH:
        console = Console()
        console.print("\n[bold green]Content Developer Results:[/bold green]")
        console.print(Panel(
            f"[bold cyan]{result.working_directory}[/bold cyan]\n\n[dim]{result.justification}[/dim]",
            title="Working Directory",
            border_style="green"
        ))
        
        phase1_status = '✅ Ready' if result.directory_ready else '❌ Not Ready'
        status_line = f"[yellow]Confidence:[/yellow] {result.confidence:.2%} | [yellow]Materials:[/yellow] {len(result.material_summaries)} | [yellow]Phase 2:[/yellow] {phase1_status}"
        
        if result.content_strategy:
            strategy_status = '✅ Ready' if result.strategy_ready else '❌ Failed'
            status_line += f" | [yellow]Strategy:[/yellow] {strategy_status}"
            console.print(Panel(
                f"[bold magenta]{result.content_strategy.summary}[/bold magenta]\n\n[dim]{result.content_strategy.thinking[:100]}...[/dim]",
                title="Content Strategy",
                border_style="magenta"
            ))
        
        if result.generation_results:
            generation_status = '✅ Ready' if result.generation_ready else '❌ Failed'
            status_line += f" | [yellow]Generation:[/yellow] {generation_status}"
            if result.generation_ready:
                create_count = sum(1 for r in result.generation_results.get('create_results', []) if r.get('success'))
                update_count = sum(1 for r in result.generation_results.get('update_results', []) if r.get('success'))
                preview_dir = result.generation_results.get('preview_dir', './llm_outputs/preview')
                
                generation_summary = f"[bold yellow]Created:[/bold yellow] {create_count} files | [bold yellow]Updated:[/bold yellow] {update_count} files"
                generation_detail = f"[dim]Preview: {preview_dir}[/dim]"
                
                console.print(Panel(
                    f"{generation_summary}\n\n{generation_detail}",
                    title="Content Generation",
                    border_style="yellow"
                ))
        
        console.print(status_line)
    else:
        print(f"\n=== Content Developer Results ===")
        print(f"Directory: {result.working_directory}")
        print(f"Justification: {result.justification}")
        
        phase2_status = 'Ready' if result.directory_ready else 'Not Ready'
        status = f"Confidence: {result.confidence:.2%} | Materials: {len(result.material_summaries)} | Phase 2: {phase2_status}"
        
        if result.content_strategy:
            strategy_status = 'Ready' if result.strategy_ready else 'Failed'
            status += f" | Strategy: {strategy_status}"
            print(f"Strategy: {result.content_strategy.summary}")
        
        if result.generation_results:
            generation_status = 'Ready' if result.generation_ready else 'Failed'
            status += f" | Generation: {generation_status}"
            if result.generation_ready:
                create_count = sum(1 for r in result.generation_results.get('create_results', []) if r.get('success'))
                update_count = sum(1 for r in result.generation_results.get('update_results', []) if r.get('success'))
                preview_dir = result.generation_results.get('preview_dir', './llm_outputs/preview')
                print(f"Generated: Created {create_count} files, Updated {update_count} files")
                print(f"Preview: {preview_dir}")
        
        print(status)
        
        if not result.directory_ready and result.setup_error:
            print(f"Error: {result.setup_error}")

# === MAIN ===
def main():
    parser = argparse.ArgumentParser(
        description="Hyper-Compact Content Developer: Repository Analysis, Content Strategy & Generation",
        epilog="""
Hyper-Compact Modular Design - Maximum reusability, minimal code
• Phase 1: Repository analysis & working directory selection
• Phase 2: Content strategy with CREATE/UPDATE recommendations
• Phase 3: Content generation for CREATE/UPDATE actions
• Intelligent LLM → Interactive fallback • Auto-confirm for CI/CD

Phases run sequentially: specifying phase N runs all phases 1 through N

Examples:
  python main.py https://github.com/Azure/azure-docs --goal "Document feature" --service compute
  python main.py https://github.com/Azure/azure-docs --goal "Storage guide" --service storage --materials doc.md --phases 3
  python main.py https://github.com/Azure/azure-docs --goal "Document Cilium" --service aks --phases 2 --apply"""
    )
    
    parser.add_argument('repo_url', help='Git repository URL')
    parser.add_argument('--goal', '-g', required=True, help='Content goal/objective')
    parser.add_argument('--service', '-s', required=True, help='Service area')
    parser.add_argument('--materials', '-m', nargs='+', default=[], help='Supporting materials')
    parser.add_argument('--phases', '-p', default='1', help='Run phases 1 through N (e.g., 3 runs phases 1, 2, and 3) (default: 1)')
    parser.add_argument('--auto-confirm', action='store_true', help='Auto-confirm LLM suggestions')
    parser.add_argument('--debug-similarity', action='store_true', help='Show detailed similarity search debugging output')
    parser.add_argument('--apply', action='store_true', help='Apply generated content to repository (default: preview only)')
    
    args = parser.parse_args()
    
    # Check git
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except:
        logger.error("Git required in PATH")
        sys.exit(1)
    
    # Execute
    try:
        config = Config(
            repo_url=args.repo_url,
            content_goal=args.goal,
            service_area=args.service,
            support_materials=args.materials,
            auto_confirm=args.auto_confirm,
            phases=args.phases,
            debug_similarity=args.debug_similarity,
            apply_changes=args.apply
        )
        result = ContentDeveloperOrchestrator(config).execute()
        display_results(result)
        
        # Report which phases were run
        max_phase = int(args.phases) if args.phases.isdigit() else 1
        if max_phase == 1:
            phases_str = "Phase 1"
        else:
            phases_str = f"Phases 1-{max_phase}"
        logger.info(f"{phases_str} completed successfully")
    except Exception as e:
        logger.error(f"Content Developer failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 