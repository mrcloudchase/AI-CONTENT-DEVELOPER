#!/bin/bash
# Test script for interactive content remediation functionality

echo "==========================================="
echo "Interactive Content Remediation Test"
echo "==========================================="
echo ""
echo "This test will run the AI Content Developer through Phase 4 (Content Remediation)"
echo "WITHOUT the --auto-confirm flag, so you can interact with each remediation step."
echo ""
echo "At each step, you can:"
echo "  y - Accept the changes"
echo "  n - Reject the changes (keep original)"
echo "  v - View the diff of changes"
echo "  d - See detailed metadata about the changes"
echo "  a - Accept all remaining changes"
echo "  s - Skip all remaining changes"
echo ""
echo "Press Enter to continue..."
read

# Set up test environment
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create a simple test material
TEST_MATERIAL="test_material_remediation.md"
cat > "$TEST_MATERIAL" << 'EOF'
# Azure Kubernetes Service Network Security

## Production Setup

To connect to your AKS cluster at IP 203.0.113.45, use the following:

```bash
az aks get-credentials --resource-group prod-rg \
  --name aks-prod-cluster \
  --subscription 12345678-1234-1234-1234-123456789012
```

Configure your storage account prodstorageacct2024:

```bash
az storage account create --name prodstorageacct2024 \
  --resource-group prod-rg \
  --location eastus
```

Contact admin@contoso.com for access.

## Network Configuration

Set up your network with these production values:
- VNet: 203.0.113.0/24
- Subnet: 203.0.113.0/27
- DNS: 8.8.8.8

Remember to use strong passwords like "P@ssw0rd123!" for all accounts.
EOF

echo "Created test material: $TEST_MATERIAL"
echo ""

# Run the tool with phases 1-4 to test remediation
echo "Running AI Content Developer (Phases 1-4)..."
echo "Note: This will use the azure-docs-pr repository as an example"
echo ""

python main.py \
  --repo https://github.com/MicrosoftDocs/azure-docs-pr \
  --goal "Create AKS network security documentation" \
  --service "Azure Kubernetes Service" \
  --materials "$TEST_MATERIAL" \
  --phases 4 \
  --work-dir ./work/test-remediation

# Clean up
echo ""
echo "Cleaning up test material..."
rm -f "$TEST_MATERIAL"

echo ""
echo "Test complete! Check ./llm_outputs/preview/ for the remediated content."
echo ""
echo "The remediation process should have:"
echo "1. SEO: Optimized titles and added meta descriptions"
echo "2. Security: Removed hardcoded IPs, credentials, and domains"
echo "3. Accuracy: Validated technical content against the material"
echo ""
echo "Each step should have shown an interactive prompt unless you selected"
echo "'a' (accept all) or 's' (skip all) during the process."
echo "===========================================" 