# Avoiding Content Truncation

## Problem
By default, the AI Content Developer applies content limits at multiple stages:
1. **Extraction phase**: Materials are truncated to `content_limit` (default: 15000 chars)
2. **Strategy phase**: Previously truncated at 5000 chars (now removed)
3. **File display**: Previously truncated at 3000 chars (now removed)

## Solution

### Quick Fix: Command Line
Set a very high content limit when running:

```bash
python main.py \
    --repo https://github.com/... \
    --goal "..." \
    --service "..." \
    -m materials.pdf \
    --content-limit 10000000  # 10 million characters
```

### Permanent Fix: Environment Variable
Add to your `.env` file:
```
# Set to a very high value to avoid truncation
CONTENT_LIMIT=10000000
```

### What We've Already Fixed
1. **Strategy material display**: No longer truncates at 5000 chars
2. **File content display**: No longer truncates at 3000 chars
3. **Top files**: Limited to 3 most relevant (from 10) to manage prompt size

## Current Behavior
- **Extraction**: Still respects `content_limit` for safety
- **Strategy prompt**: Shows complete content (no truncation)
- **File analysis**: Shows complete content (no truncation)

## Recommendations
- For most use cases, `--content-limit 1000000` (1M chars) is sufficient
- For very large PDFs or documents, increase as needed
- Monitor Azure OpenAI token limits when using very large content 