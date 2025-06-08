# Troubleshooting Guide

## Common Errors and Solutions

### Phase 3: Content Generation Errors

#### Error: `'Config' object has no attribute 'check_material_sufficiency'`

**Symptoms:**
```
ERROR Phase 3 failed: 'Config' object has no attribute 'check_material_sufficiency'
```

**Cause:**
The Config model was missing the `check_material_sufficiency` attribute that the ContentGenerationProcessor tries to access.

**Solution:**
This has been fixed by adding `check_material_sufficiency: bool = True` to the Config model. The material sufficiency check now:
- Runs by default after content creation/updates
- Evaluates if provided materials contain enough information
- Reports coverage percentage and confidence
- Suggests additional materials if needed

**To disable material sufficiency checks:**
Set `check_material_sufficiency=False` in your Config or use a command-line flag if available.

#### Error: `get_update_content_prompt() missing required positional arguments`

**Symptoms:**
```
ERROR Phase 3 failed: get_update_content_prompt() missing 3 required positional arguments: 'chunk_context', 'content_type_info', and 'content_standards'
```

**Cause:**
The ContentGenerationProcessor was not passing all required parameters to the update prompt function.

**Solution:**
This has been fixed in the latest version. The fix ensures all 7 required parameters are passed:
- config
- action (converted from ContentDecision)
- existing_content
- material_context
- chunk_context
- content_type_info (extracted from document)
- content_standards

**If you encounter this error:**
1. Ensure you have the latest code
2. Check that `processors/generation.py` has the updated `_update_content` method
3. Run `scripts/test_phase3_fix.sh` to verify the fix

### Phase 1: Repository Analysis Errors

#### Error: Directory not found
**Cause:** The selected directory path is incorrect or doesn't exist.
**Solution:** Check the repository structure and ensure the directory exists.

### Phase 2: Content Strategy Errors

#### Error: No relevant files found
**Cause:** The embeddings search didn't find any relevant files.
**Solution:** 
- Check that the repository has markdown files
- Verify the service area matches the repository content
- Try with a different content goal

### Authentication Errors

#### Error: DefaultAzureCredential failed
**Solution:**
1. Run `az login`
2. Check `az account show`
3. Verify access to Azure OpenAI resource

### Material Extraction Errors

#### Error: Content truncated
**Solution:** Use `--content-limit 10000000` to avoid truncation

### Material Sufficiency Issues

#### Problem: Content generation skipped due to insufficient materials
**Symptoms:**
```
❌ Insufficient Materials
Material coverage too low: 25%
```

**Cause:**
The pre-generation material sufficiency check determined that the provided materials don't contain enough information to generate quality content.

**Solution:**
1. Review the missing topics listed in the error message
2. Add the suggested materials to your input
3. Ensure materials include:
   - Technical specifications
   - Implementation details  
   - Code examples
   - Best practices
4. Re-run with updated materials

**To bypass the check (not recommended):**
Set `check_material_sufficiency=False` in config, but this may result in low-quality content.

#### Problem: Materials seem sufficient but still getting low coverage
**Cause:** Materials may be truncated or not properly extracted.

**Solution:**
1. Increase content limit: `--content-limit 10000000`
2. Check material extraction in `llm_outputs/phase-01/`
3. Verify PDFs/documents are text-extractable
4. For web materials, ensure full page loads

## Debug Tips

1. **Enable debug mode:**
   ```bash
   export AI_CONTENT_DEBUG=true
   ```

2. **Check logs:**
   - Look in `./llm_outputs/` for detailed logs
   - Check `logs/app.log` for system logs

3. **Run health check:**
   ```bash
   ./scripts/health_check.sh
   ``` 