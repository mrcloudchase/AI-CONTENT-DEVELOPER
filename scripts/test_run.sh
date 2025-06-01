#!/bin/bash
# AI Content Developer Test Run Script
# Tests basic functionality with minimal inputs

echo "=== AI Content Developer Test Run ==="
echo "This will test basic functionality with AKS documentation materials."
echo ""

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    echo "Please run: export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

# Use the actual test file and URL
test_file="./inputs/aks-prd-02.docx"
test_url="https://learn.microsoft.com/en-us/azure/aks/azure-cni-powered-by-cilium"
repo_url="https://github.com/MicrosoftDocs/azure-aks-docs"

# Check if test file exists
if [ ! -f "$test_file" ]; then
    echo "❌ Error: Test file not found: $test_file"
    exit 1
fi

echo "Using test materials:"
echo "  - File: $test_file"
echo "  - URL: $test_url"
echo ""

# Phase 1 Test
echo "=== Testing Phase 1: Repository Analysis ==="
python main.py \
    "$repo_url" \
    "Document Cilium networking for AKS" \
    "Azure Kubernetes Service" \
    "$test_file" \
    "$test_url" \
    --phases 1 \
    --auto-confirm

phase1_result=$?

if [ $phase1_result -eq 0 ]; then
    echo "✅ Phase 1 completed successfully"
else
    echo "❌ Phase 1 failed with exit code: $phase1_result"
    exit $phase1_result
fi

# Check outputs
echo ""
echo "Checking Phase 1 outputs:"
if [ -d "llm_outputs/materials_summary" ]; then
    echo "  ✓ Materials summary directory created"
    file_count=$(ls -1 llm_outputs/materials_summary/*.json 2>/dev/null | wc -l)
    echo "  ✓ Found $file_count interaction file(s)"
else
    echo "  ✗ Materials summary directory not found"
fi

if [ -d "work/tmp" ]; then
    echo "  ✓ Repository cloned/updated"
else
    echo "  ✗ Repository directory not found"
fi

# Phase 2 Test
echo ""
echo "=== Testing Phase 2: Content Discovery ==="
python main.py \
    "$repo_url" \
    "Document Cilium networking for AKS" \
    "Azure Kubernetes Service" \
    "$test_file" \
    "$test_url" \
    --phases 2 \
    --auto-confirm

phase2_result=$?

if [ $phase2_result -eq 0 ]; then
    echo "✅ Phase 2 completed successfully"
else
    echo "❌ Phase 2 failed with exit code: $phase2_result"
fi

# Check Phase 2 outputs
echo ""
echo "Checking Phase 2 outputs:"
if [ -d "llm_outputs/embeddings" ]; then
    echo "  ✓ Embeddings directory created"
    cache_count=$(ls -1 llm_outputs/embeddings/*.json 2>/dev/null | wc -l)
    echo "  ✓ Found $cache_count embedding cache file(s)"
else
    echo "  ✗ Embeddings directory not found"
fi

if [ -d "llm_outputs/content_strategy" ]; then
    echo "  ✓ Content strategy directory created"
    strategy_count=$(ls -1 llm_outputs/content_strategy/*.json 2>/dev/null | wc -l)
    echo "  ✓ Found $strategy_count strategy file(s)"
else
    echo "  ✗ Content strategy directory not found"
fi

# Phase 3 Test
echo ""
echo "=== Testing Phase 3: Content Generation ==="
python main.py \
    "$repo_url" \
    "Document Cilium networking for AKS" \
    "Azure Kubernetes Service" \
    "$test_file" \
    "$test_url" \
    --phases 3 \
    --auto-confirm

phase3_result=$?

if [ $phase3_result -eq 0 ]; then
    echo "✅ Phase 3 completed successfully"
else
    echo "❌ Phase 3 failed with exit code: $phase3_result"
fi

# Check Phase 3 outputs
echo ""
echo "Checking Phase 3 outputs:"
if [ -d "llm_outputs/preview" ]; then
    echo "  ✓ Preview directory created"
    preview_count=$(ls -1 llm_outputs/preview/*.md 2>/dev/null | wc -l)
    echo "  ✓ Found $preview_count generated content file(s)"
    
    # Show generated files
    if [ $preview_count -gt 0 ]; then
        echo ""
        echo "Generated files:"
        ls -la llm_outputs/preview/*.md 2>/dev/null | tail -5
    fi
else
    echo "  ✗ Preview directory not found"
fi

# Summary
echo ""
echo "=== Test Summary ==="
total_errors=0
if [ $phase1_result -ne 0 ]; then
    echo "❌ Phase 1: Failed"
    ((total_errors++))
else
    echo "✅ Phase 1: Passed"
fi

if [ $phase2_result -ne 0 ]; then
    echo "❌ Phase 2: Failed"
    ((total_errors++))
else
    echo "✅ Phase 2: Passed"
fi

if [ $phase3_result -ne 0 ]; then
    echo "❌ Phase 3: Failed"
    ((total_errors++))
else
    echo "✅ Phase 3: Passed"
fi

echo ""
if [ $total_errors -eq 0 ]; then
    echo "🎉 All tests passed! The application is working correctly."
    exit 0
else
    echo "❌ $total_errors phase(s) failed. Check the logs above for details."
    exit 1
fi 