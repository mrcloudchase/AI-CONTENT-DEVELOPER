# Large Repository Handling

## Overview

The AI Content Developer automatically optimizes structure display for large repositories to prevent rate limiting while maintaining full visibility.

## How It Works

### Automatic Detection
- Repositories with >5,000 files are detected as "large"
- The tool automatically switches to directory-only view
- No user intervention required

### Directory-Only Structure
All repositories now use a directory-only tree view by default:
- Shows complete directory hierarchy (all directories, all depths)
- Excludes individual files to reduce prompt size
- Displays markdown file count for each directory
- Indicates TOC.yml presence with [TOC] tag

### Smart Filtering
Common non-documentation directories are automatically excluded:
- Build directories: `node_modules`, `dist`, `build`, `target`
- Test directories: `test`, `tests`, `__pycache__`, `coverage`
- Media directories: `media`, `images`, `assets`, `static`
- Vendor directories: `vendor`, `dependencies`
- Version control: `.git`

## Example Output

```
[Repository Root] (5 .md)
├── articles [TOC] (0 .md)
│   ├── aks (45 .md)
│   │   ├── concepts (12 .md)
│   │   ├── how-to (20 .md)
│   │   └── troubleshooting (13 .md)
│   ├── storage (32 .md)
│   │   ├── blobs (15 .md)
│   │   ├── files (10 .md)
│   │   └── queues (7 .md)
│   └── app-service (28 .md)
│       ├── quickstarts (5 .md)
│       ├── tutorials (10 .md)
│       └── reference (13 .md)
├── includes (523 .md)
└── bread (0 .md)
```

## Benefits

1. **Performance**: Reduces prompt size significantly for large repos
2. **Visibility**: Still shows complete directory structure
3. **Context**: Markdown file counts help identify documentation areas
4. **Rate Limit Prevention**: Avoids hitting Azure OpenAI token limits

## Implementation Details

The feature is implemented in:
- `content_developer/repository/manager.py`: `get_directory_structure()` method
- `content_developer/orchestrator/orchestrator.py`: Large repo detection logic

## Advanced Features

### Condensed View (Optional)
A `get_condensed_structure()` method is available for extreme cases where even the directory tree is too large. This method:
- Shows only top documentation directories
- Ranks by relevance to service area
- Provides summary statistics

This is not used by default but remains available for future use.

### Custom Depth Control
The `max_depth` parameter (default: 3) controls how deep the directory tree goes:
```bash
python main.py ... --max-depth 5  # Show 5 levels deep
``` 