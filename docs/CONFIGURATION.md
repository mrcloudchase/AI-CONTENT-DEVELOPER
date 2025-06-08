# AI Content Developer - Configuration Guide

## Overview

This guide covers all configuration options for AI Content Developer, including environment variables, command-line arguments, model configuration, and content standards.

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with these settings:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Optional: API Version (defaults shown)
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Optional: Temperature Settings
AZURE_OPENAI_TEMPERATURE=0.3
AZURE_OPENAI_CREATIVE_TEMPERATURE=0.7
```

### Environment Variable Details

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI resource endpoint URL | Yes | None |
| `AZURE_OPENAI_COMPLETION_DEPLOYMENT` | Deployment name for completion model | Yes | None |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment name for embedding model | Yes | None |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | No | "2024-08-01-preview" |
| `AZURE_OPENAI_TEMPERATURE` | Temperature for standard operations | No | 0.3 |
| `AZURE_OPENAI_CREATIVE_TEMPERATURE` | Temperature for creative operations | No | 0.7 |

## Command Line Configuration

### Basic Syntax

```bash
python main.py --repo <url> --goal "<goal>" --service "<service>" -m [materials...]
```

### Required Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--repo` | | Repository URL to analyze | `https://github.com/Azure/azure-docs` |
| `--goal` | | Content creation/update goal | `"Create Kubernetes networking guide"` |
| `--service` | | Azure service area | `"Azure Kubernetes Service"` |
| `--materials` | `-m` | Support material files/URLs | `guide.pdf spec.docx` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--audience` | "technical professionals" | Target audience |
| `--audience-level` | "intermediate" | Technical level (beginner/intermediate/advanced) |
| `--auto-confirm` | False | Skip all confirmation prompts |
| `--apply-changes` | False | Apply changes to repository |
| `--clean` | False | Clear outputs before starting |
| `--work-dir` | "./work/tmp" | Working directory for repos |
| `--max-depth` | 3 | Max repository analysis depth |
| `--content-limit` | 15000 | Material extraction character limit |
| `--phases` | "all" | Phases to run (see Phase Configuration) |
| `--debug-similarity` | False | Show similarity scoring details |
| `--skip-toc` | False | Skip TOC management phase |

## Phase Configuration

### Phase Selection

Use `--phases` to control which phases run:

#### Single Phases
- `1` - Repository Analysis only
- `2` - Content Strategy only
- `3` - Content Generation only
- `4` - Content Remediation only
- `5` - TOC Management only

#### Phase Combinations
- `12` - Analysis + Strategy
- `23` - Strategy + Generation
- `34` - Generation + Remediation
- `45` - Remediation + TOC
- `123` - Analysis through Generation
- `234` - Strategy through Remediation
- `345` - Generation through TOC
- `1234` - All except TOC
- `2345` - All except Analysis
- `all` or `12345` - All phases

### Phase Dependencies

Some phases require prior phases to have completed:
- Phase 2 requires Phase 1 results
- Phase 3 requires Phase 2 results
- Phase 4 requires Phase 3 results
- Phase 5 requires Phase 3 results (can run without Phase 4)

## Model Configuration

### Supported Models

#### Completion Models
- `gpt-4` - Standard GPT-4
- `gpt-4o` - Optimized GPT-4 (recommended)
- `gpt-4.1` - Latest GPT-4 version
- `gpt-35-turbo` - Faster, lower cost option

#### Embedding Models
- `text-embedding-3-small` - Efficient, recommended
- `text-embedding-3-large` - Higher dimension embeddings
- `text-embedding-ada-002` - Legacy model

### Model Selection Criteria

Choose models based on:
- **Quality Requirements**: GPT-4 variants for best results
- **Speed**: GPT-3.5-turbo for faster processing
- **Cost**: Consider token pricing for your use case
- **Availability**: Check regional availability

## Content Standards Configuration

### content_standards.json Structure

```json
{
  "contentTypes": [
    {
      "id": "howto",
      "name": "How-To Guide",
      "purpose": "Step-by-step instructions",
      "structure": [
        "## Prerequisites",
        "## Steps",
        "## Next steps"
      ],
      "frontMatter": {
        "ms.topic": "how-to"
      }
    }
  ],
  "formattingElements": [...],
  "codeGuidelines": {...}
}
```

### Content Type Configuration

Each content type should define:
- `id`: Unique identifier
- `name`: Display name
- `purpose`: When to use this type
- `description`: Detailed description
- `structure`: Required sections
- `frontMatter`: Metadata requirements

### Adding Custom Content Types

1. Edit `content_standards.json`
2. Add new type to `contentTypes` array
3. Define all required fields
4. Restart application

## Cache Configuration

### Cache Location

Embeddings and chunks are cached in:
```
./llm_outputs/embeddings/[repo_name]/[working_directory]/
```

### Cache Management

#### Clear All Cache
```bash
./scripts/reset.sh cache
```

#### Clear Specific Repository Cache
```bash
rm -rf ./llm_outputs/embeddings/[repo_name]/
```

#### Cache Size Management
Monitor cache size:
```bash
du -sh ./llm_outputs/embeddings/
```

## Logging Configuration

### Log Levels

Set via environment variable:
```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Log Files

Logs are stored in:
```
./logs/ai_content_developer_[timestamp].log
```

### Log Rotation

Logs rotate when they reach 10MB, keeping last 5 files.

## Authentication Configuration

### Azure CLI (Recommended)

```bash
# Login
az login

# Set subscription
az account set --subscription "Your Subscription"
```

### Service Principal

```bash
export AZURE_CLIENT_ID="your-sp-id"
export AZURE_CLIENT_SECRET="your-sp-secret" 
export AZURE_TENANT_ID="your-tenant-id"
```

### Managed Identity

No configuration needed when running in Azure with assigned identity.

## Performance Tuning

### Parallel Processing

Control concurrent operations:
```python
# In content_developer/processors/discovery.py
ThreadPoolExecutor(max_workers=4)  # Adjust based on system
```

### Token Limits

Adjust context windows:
```python
# In content_developer/constants.py
CHUNK_SIZE = 1000  # Characters per chunk
MAX_CHUNKS_PER_FILE = 50  # Limit chunks per file
```

### Rate Limiting

Handle Azure OpenAI rate limits:
```python
# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
```

## Advanced Configuration

### Custom Prompts

Override default prompts by creating:
```
./prompts/custom/[phase]/[prompt_name].py
```

### Processor Configuration

Configure processor behavior:
```python
# In processors
self.config.max_similarity_results = 5
self.config.similarity_threshold = 0.7
```

### Repository Filters

Exclude directories from analysis:
```python
# In repository/manager.py
EXCLUDED_DIRS = [
    'node_modules', 'dist', 'build',
    '.git', '__pycache__', 'venv'
]
```

## Configuration Best Practices

### 1. Environment Management

Use different `.env` files for different environments:
```bash
.env.development
.env.production
.env.test
```

### 2. Secure Credentials

Never commit `.env` files:
```bash
# .gitignore
.env*
!.env.example
```

### 3. Model Selection

- Development: Use cheaper models (gpt-35-turbo)
- Production: Use best models (gpt-4o)
- Testing: Mock responses when possible

### 4. Phase Selection

- Initial runs: Use phase 1 only to verify setup
- Iterative development: Run phases 2-3 repeatedly
- Final runs: Use all phases for complete workflow

### 5. Material Limits

- Small materials (<1MB): Default settings
- Large materials (>10MB): Increase `--content-limit`
- Very large materials: Split into multiple files

## Troubleshooting Configuration

### Common Issues

1. **Missing Environment Variables**
   ```
   Error: AZURE_OPENAI_ENDPOINT not set
   ```
   Solution: Ensure `.env` file exists and is loaded

2. **Invalid Model Names**
   ```
   Error: Deployment 'gpt-4' not found
   ```
   Solution: Verify deployment names match Azure portal

3. **Authentication Failures**
   ```
   Error: DefaultAzureCredential failed
   ```
   Solution: Run `az login` and verify subscription

4. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   ```
   Solution: Reduce parallel operations or add delays

### Configuration Validation

Run health check:
```bash
./scripts/health_check.sh
```

This validates:
- Environment variables
- Azure connectivity
- Model deployments
- File permissions

## Configuration Examples

### High-Quality Documentation

```bash
python main.py \
    --repo https://github.com/Azure/azure-docs \
    --goal "Create comprehensive guide" \
    --service "Azure Kubernetes Service" \
    -m detailed-spec.pdf \
    --phases all \
    --content-limit 10000000 \
    --apply-changes
```

### Quick Preview

```bash
python main.py \
    --repo https://github.com/Azure/azure-docs \
    --goal "Update existing docs" \
    --service "Azure Storage" \
    -m updates.md \
    --phases 123 \
    --auto-confirm
```

### Debugging Run

```bash
LOG_LEVEL=DEBUG python main.py \
    --repo https://github.com/test/repo \
    --goal "Test configuration" \
    --service "Test Service" \
    -m test.md \
    --phases 1 \
    --debug-similarity
``` 