# AI Content Developer - Troubleshooting Guide

## Quick Diagnostics

Run the health check script first:
```bash
./scripts/health_check.sh
```

This will verify:
- Python version compatibility
- Azure CLI authentication
- Environment variables
- Azure OpenAI connectivity
- Model deployments
- File permissions

## Common Issues and Solutions

### 1. Authentication Errors

#### Error: "DefaultAzureCredential failed to retrieve a token"

**Symptoms:**
```
azure.core.exceptions.ClientAuthenticationError: DefaultAzureCredential failed to retrieve a token
```

**Solutions:**

1. **Ensure Azure CLI is logged in:**
   ```bash
   az login
   az account show
   ```

2. **Check subscription:**
   ```bash
   az account list --output table
   az account set --subscription "Your Subscription Name"
   ```

3. **Verify permissions:**
   ```bash
   # Check your role assignments
   az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --output table
   ```

4. **Clear Azure CLI cache:**
   ```bash
   az account clear
   az login
   ```

### 2. Model Deployment Errors

#### Error: "The API deployment for this resource does not exist"

**Symptoms:**
```
openai.NotFoundError: Error code: 404 - The API deployment for this resource does not exist
```

**Solutions:**

1. **Verify deployment names:**
   ```bash
   # List deployments
   az cognitiveservices account deployment list \
       --name YourOpenAIResource \
       --resource-group YourResourceGroup \
       --output table
   ```

2. **Check .env file:**
   ```bash
   # Ensure deployment names match exactly
   AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-4o  # Must match Azure portal
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
   ```

3. **Verify endpoint URL:**
   ```bash
   # Should end with trailing slash
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

### 3. Content Generation Errors

#### Error: "Missing: Detailed explanation and configuration steps"

**Symptoms:**
- Material sufficiency check fails
- Generated content lacks detail
- Incomplete documentation

**Solutions:**

1. **Provide more comprehensive materials:**
   ```bash
   # Use multiple detailed sources
   python main.py ... -m detailed-spec.pdf technical-guide.docx examples.md
   ```

2. **Increase content limit:**
   ```bash
   # For large materials
   python main.py ... --content-limit 10000000
   ```

3. **Check material extraction:**
   ```bash
   # Look for extraction errors in logs
   grep "Failed to extract" ./logs/ai_content_developer_*.log
   ```

### 4. Phase-Specific Errors

#### Phase 1: Directory Selection Issues

**Error: "Markdown Files: 0"**

**Solutions:**

1. **Verify directory structure:**
   ```bash
   # Check if markdown files exist
   find ./repositories/[repo] -name "*.md" | head -20
   ```

2. **Manual directory override:**
   - When prompted, manually select the correct directory
   - Ensure you're selecting a directory, not a file

#### Phase 2: Strategy Generation Failures

**Error: "KeyError: 'id'"**

**Solutions:**

1. **Update content_standards.json:**
   ```json
   {
     "contentTypes": [
       {
         "id": "howto",  // Ensure 'id' field exists
         "name": "How-To Guide",
         ...
       }
     ]
   }
   ```

2. **Clear strategy cache:**
   ```bash
   rm -rf ./llm_outputs/content_strategy/
   ```

#### Phase 3: Content Generation Errors

**Error: "get_create_content_prompt() missing required arguments"**

**Solutions:**

1. **Update to latest code:**
   ```bash
   git pull origin main
   ```

2. **Check prompt imports:**
   - Ensure all prompt functions are properly imported
   - Verify phase3 prompts are accessible

#### Phase 4: Remediation Failures

**Error: "No preview files found"**

**Solutions:**

1. **Ensure Phase 3 completed:**
   ```bash
   # Check preview directory
   ls -la ./llm_outputs/preview/create/
   ls -la ./llm_outputs/preview/update/
   ```

2. **Run phases sequentially:**
   ```bash
   python main.py ... --phases 123  # Then run phase 4
   ```

#### Phase 5: TOC Management Errors

**Error: "Failed to parse TOC.yml"**

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Install yamllint if needed
   pip install yamllint
   yamllint [repo]/TOC.yml
   ```

2. **Skip TOC phase:**
   ```bash
   python main.py ... --skip-toc
   ```

3. **Common YAML issues:**
   - Use spaces, not tabs
   - Ensure proper indentation (2 spaces)
   - Check for duplicate keys

### 5. Performance Issues

#### Slow Processing

**Solutions:**

1. **Reduce parallel operations:**
   ```python
   # In discovery.py
   ThreadPoolExecutor(max_workers=2)  # Reduce from 4
   ```

2. **Use cached embeddings:**
   ```bash
   # Don't clear cache unnecessarily
   # Embeddings are reused for unchanged files
   ```

3. **Process smaller batches:**
   ```bash
   # Run specific phases
   python main.py ... --phases 12  # Strategy only
   ```

#### Rate Limiting

**Error: "Rate limit reached for requests"**

**Solutions:**

1. **Wait and retry:**
   ```bash
   # Azure OpenAI has per-minute limits
   sleep 60
   python main.py ...
   ```

2. **Increase deployment capacity:**
   - Go to Azure Portal
   - Navigate to your OpenAI resource
   - Increase TPM (Tokens Per Minute) for deployments

3. **Use different models for development:**
   ```bash
   # Use gpt-35-turbo for testing
   AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo
   ```

### 6. Environment Issues

#### Python Version Incompatibility

**Error: "ModuleNotFoundError" or dependency conflicts**

**Solutions:**

1. **Use Python 3.12 or earlier:**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Clean virtual environment:**
   ```bash
   deactivate
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### Missing Dependencies

**Solutions:**

1. **Install all requirements:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Check for system dependencies:**
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install python3-dev build-essential
   
   # For macOS
   brew install python@3.12
   ```

### 7. Cache Issues

#### Corrupted Cache

**Symptoms:**
- "Failed to create DocumentChunk from cache"
- Unexpected embedding errors

**Solutions:**

1. **Clear specific repository cache:**
   ```bash
   rm -rf ./llm_outputs/embeddings/[repo_name]/
   ```

2. **Reset all cache:**
   ```bash
   ./scripts/reset.sh cache
   ```

3. **Validate cache integrity:**
   ```bash
   python -c "from content_developer.cache import UnifiedCache; 
   cache = UnifiedCache('./llm_outputs/embeddings/repo/dir'); 
   cache.verify_and_cleanup_manifest()"
   ```

### 8. Material Processing Errors

#### PDF Extraction Failures

**Solutions:**

1. **Check PDF validity:**
   ```bash
   # Install pdfinfo
   pdfinfo your-material.pdf
   ```

2. **Try alternative extraction:**
   ```bash
   # Convert to text first
   pdftotext your-material.pdf material.txt
   python main.py ... -m material.txt
   ```

#### URL Access Errors

**Solutions:**

1. **Verify URL accessibility:**
   ```bash
   curl -I https://your-url.com
   ```

2. **Use local copy:**
   ```bash
   # Download first
   wget https://your-url.com -O material.html
   python main.py ... -m material.html
   ```

## Debug Techniques

### 1. Enable Verbose Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG
export AI_CONTENT_DEBUG=true

# Or use command line
python main.py ... --debug-similarity
```

### 2. Check Specific Phase Logs

```bash
# Phase 1 logs
grep "Phase 1" ./logs/ai_content_developer_*.log

# LLM interactions
ls -la ./llm_outputs/
```

### 3. Test Individual Components

```python
# Test material extraction
from content_developer.extraction import ContentExtractor
extractor = ContentExtractor()
content = extractor.extract_content("test.pdf")
print(content[:500])

# Test embeddings
from content_developer.processors import ContentDiscoveryProcessor
processor = ContentDiscoveryProcessor(client, config)
# ... test processing
```

### 4. Validate Configuration

```python
# Check environment
import os
from dotenv import load_dotenv
load_dotenv()

print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"Completion: {os.getenv('AZURE_OPENAI_COMPLETION_DEPLOYMENT')}")
print(f"Embedding: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}")
```

## Reset and Recovery

### Full Reset

```bash
# Complete reset
./scripts/reset.sh full

# This removes:
# - All cached embeddings
# - Generated content
# - Preview files
# - Cloned repositories
```

### Selective Reset

```bash
# Reset outputs only
./scripts/reset.sh outputs

# Reset cache only
./scripts/reset.sh cache

# Reset specific phase
rm -rf ./llm_outputs/content_strategy/
rm -rf ./llm_outputs/preview/
```

### Recovery Steps

1. **After errors:**
   ```bash
   # Check last successful phase
   grep "Phase .* completed" ./logs/ai_content_developer_*.log | tail -5
   
   # Resume from next phase
   python main.py ... --phases [next_phase]
   ```

2. **Partial results:**
   ```bash
   # Preview generated content
   ls -la ./llm_outputs/preview/
   
   # Apply manually if needed
   cp ./llm_outputs/preview/create/*.md [target_directory]/
   ```

## Getting Help

### 1. Check Logs

```bash
# Latest log
ls -t ./logs/*.log | head -1 | xargs tail -100

# Search for errors
grep -i error ./logs/ai_content_developer_*.log | tail -20
```

### 2. Community Support

- GitHub Issues: Report bugs with logs
- Discussions: Ask questions
- Wiki: Check for solutions

### 3. Diagnostic Information

When reporting issues, include:

```bash
# System info
python --version
az --version

# Environment (sanitized)
env | grep AZURE_OPENAI | sed 's/=.*/=***/'

# Error logs
tail -50 ./logs/ai_content_developer_*.log

# Command used (sanitized)
python main.py --repo *** --goal "***" ...
```

## Prevention Tips

1. **Start Small:**
   - Test with phase 1 first
   - Use small materials initially
   - Verify each phase works

2. **Monitor Resources:**
   - Check Azure costs regularly
   - Monitor rate limits
   - Track cache size

3. **Backup Important Data:**
   - Save generated content
   - Export successful strategies
   - Version control your docs

4. **Use Preview Mode:**
   - Always preview before --apply-changes
   - Review generated content
   - Test on non-production repos first 