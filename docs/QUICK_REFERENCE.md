# AI Content Developer - Quick Reference

## Quick Commands

### Basic Run
```bash
python main.py --repo <repo_url> --goal "<goal>" --service "<service>" -m <materials>
```

### Common Scenarios

#### Test Setup (Phase 1 only)
```bash
python main.py \
    --repo https://github.com/MicrosoftDocs/azure-aks-docs \
    --goal "Test setup" \
    --service "Azure Kubernetes Service" \
    -m test.md \
    --phases 1
```

#### Generate Strategy Without Content (Phases 1-2)
```bash
python main.py \
    --repo <repo_url> \
    --goal "<goal>" \
    --service "<service>" \
    -m <materials> \
    --phases 12 \
    --auto-confirm
```

#### Full Workflow with Auto-Apply
```bash
python main.py \
    --repo <repo_url> \
    --goal "<goal>" \
    --service "<service>" \
    -m <materials> \
    --phases all \
    --auto-confirm \
    --apply-changes
```

## Phase Reference

| Phase | Name | Purpose | Output |
|-------|------|---------|--------|
| 1 | Repository Analysis | Clone repo, analyze structure, select directory | Working directory selection |
| 2 | Content Strategy | Analyze gaps, plan changes | CREATE/UPDATE/SKIP decisions |
| 3 | Content Generation | Generate new content, update existing | Preview files |
| 4 | Content Remediation | SEO, Security, Accuracy improvements | Remediated preview files |
| 5 | TOC Management | Update table of contents | Updated TOC.yml |

## Common Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--phases 123` | Run specific phases | Run phases 1, 2, and 3 |
| `--auto-confirm` | Skip all prompts | Useful for automation |
| `--apply-changes` | Apply to repository | Actually write files |
| `--skip-toc` | Skip Phase 5 | If TOC.yml is invalid |
| `--clean` | Fresh start | Clear all outputs |
| `--debug-similarity` | Debug mode | Show scoring details |
| `--content-limit 10000000` | No truncation | For large materials |

## Material Types

| Type | Extension | Example |
|------|-----------|---------|
| PDF | .pdf | `guide.pdf` |
| Word | .docx, .doc | `spec.docx` |
| Markdown | .md | `readme.md` |
| Web | http/https | `https://docs.microsoft.com/...` |
| Text | .txt | `notes.txt` |

## Environment Variables

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Optional
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_TEMPERATURE=0.3
AZURE_OPENAI_CREATIVE_TEMPERATURE=0.7
LOG_LEVEL=INFO
```

## Directory Structure

```
./llm_outputs/
├── materials_summary/      # Material analysis
├── decisions/             # Directory selection
├── content_strategy/      # Strategy results
├── embeddings/           # Cached embeddings
├── preview/              # Generated content
│   ├── create/          # New files
│   └── update/          # Updated files
└── toc_management/       # TOC updates
```

## Troubleshooting Commands

### Check Setup
```bash
./scripts/health_check.sh
```

### Reset Cache
```bash
./scripts/reset.sh cache
```

### Clear All Outputs
```bash
./scripts/reset.sh full
```

### Test Run
```bash
./scripts/test_run.sh
```

### Check Logs
```bash
# Latest log
ls -t ./logs/*.log | head -1 | xargs tail -f

# Search errors
grep -i error ./logs/*.log | tail -20
```

## Performance Tips

1. **Use Cached Embeddings**: Don't clear cache unnecessarily
2. **Run Phases Incrementally**: Test each phase before running all
3. **Preview First**: Always preview before `--apply-changes`
4. **Limit Materials**: Start with focused materials, add more if needed
5. **Monitor Logs**: Keep terminal open with `tail -f` on latest log

## Common Errors

| Error | Solution |
|-------|----------|
| "DefaultAzureCredential failed" | Run `az login` |
| "Deployment not found" | Check deployment names in .env |
| "No materials provided" | Ensure material paths are correct |
| "Rate limit exceeded" | Wait 60 seconds and retry |
| "TOC parse failed" | Use `--skip-toc` flag |

## Best Practices

1. **Start Small**: Test with one material and phase 1
2. **Validate Each Phase**: Ensure output is correct before proceeding
3. **Use Version Control**: Commit before running with `--apply-changes`
4. **Review Strategy**: Always check Phase 2 decisions
5. **Check Preview**: Review generated content before applying

## Advanced Usage

### Custom Working Directory
```bash
--work-dir ./my-repos
```

### Specific Repository Depth
```bash
--max-depth 5
```

### Different Audience Levels
```bash
--audience "cloud architects" --audience-level advanced
```

### Multiple Materials with URLs
```bash
-m spec.pdf guide.docx https://learn.microsoft.com/... notes.md
```

## Debugging

### Enable All Debug Output
```bash
export LOG_LEVEL=DEBUG
export AI_CONTENT_DEBUG=true
python main.py ... --debug-similarity
```

### Check Specific Phase Output
```bash
# Phase 2 strategy
cat ./llm_outputs/content_strategy/*.json | jq .

# Phase 3 preview
ls -la ./llm_outputs/preview/
```

### Validate Cache
```bash
find ./llm_outputs/embeddings -name "*.json" | wc -l
``` 