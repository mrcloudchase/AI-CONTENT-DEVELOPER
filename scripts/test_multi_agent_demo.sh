#!/bin/bash
# Test Multi-Agent Content Developer Demo
# This script demonstrates the multi-agent system with a simple example

set -e

echo "🚀 Multi-Agent Content Developer Demo"
echo "===================================="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with:"
    echo "  PROJECT_ENDPOINT=https://your-project.azureai.io"
    echo "  MODEL_DEPLOYMENT_NAME=your-deployment-name"
    exit 1
fi

# Check if PROJECT_ENDPOINT is set
if ! grep -q "PROJECT_ENDPOINT=" .env || grep -q "PROJECT_ENDPOINT=$" .env; then
    echo "❌ Error: PROJECT_ENDPOINT not configured in .env"
    echo "Please add: PROJECT_ENDPOINT=https://your-project.azureai.io"
    exit 1
fi

# Check if MODEL_DEPLOYMENT_NAME is set
if ! grep -q "MODEL_DEPLOYMENT_NAME=" .env || grep -q "MODEL_DEPLOYMENT_NAME=$" .env; then
    echo "❌ Error: MODEL_DEPLOYMENT_NAME not configured in .env"
    echo "Please add: MODEL_DEPLOYMENT_NAME=your-deployment-name"
    exit 1
fi

# First run the test script
echo "🧪 Running multi-agent tests..."
python test_multi_agent.py

if [ $? -ne 0 ]; then
    echo "❌ Multi-agent tests failed. Please fix the issues above."
    exit 1
fi

echo
echo "✅ Tests passed! Now running a demo..."
echo

# Create a test material if it doesn't exist
MATERIAL_DIR="test_materials"
MATERIAL_FILE="$MATERIAL_DIR/sample_networking.md"

if [ ! -f "$MATERIAL_FILE" ]; then
    echo "📝 Creating sample material..."
    mkdir -p "$MATERIAL_DIR"
    cat > "$MATERIAL_FILE" << 'EOF'
# Azure Kubernetes Service Networking Overview

## Introduction
Azure Kubernetes Service (AKS) provides several networking options to connect your applications and services.

## Network Models
AKS supports two network models:
- **Kubenet**: Basic networking with limited features
- **Azure CNI**: Advanced networking with full Azure Virtual Network integration

## Key Features
- Pod-to-pod communication
- Service discovery via DNS
- Load balancing with Azure Load Balancer
- Ingress controllers for HTTP/HTTPS routing
- Network policies for security

## Best Practices
1. Use Azure CNI for production workloads
2. Implement network policies
3. Use private endpoints for secure access
4. Monitor network performance

## Common Scenarios
- Multi-tier applications
- Microservices architecture
- Hybrid cloud connectivity
EOF
    echo "✅ Sample material created at: $MATERIAL_FILE"
fi

# Run the multi-agent demo
echo
echo "🤖 Running Multi-Agent Content Developer..."
echo "Goal: Create a guide for AKS networking basics"
echo

# Use a simple public repo for testing
DEMO_COMMAND="python main.py \
    https://github.com/MicrosoftDocs/azure-docs \
    'Create a beginner-friendly guide for AKS networking basics' \
    'aks' \
    '$MATERIAL_FILE' \
    --multi-agent \
    --auto-confirm \
    --phases 1-2"

echo "Command:"
echo "$DEMO_COMMAND"
echo
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Execute the demo
eval $DEMO_COMMAND

echo
echo "🎉 Demo completed!"
echo
echo "Check the following for results:"
echo "  - llm_outputs/orchestrator_output.md - Full orchestrator output"
echo "  - llm_outputs/strategy/ - Strategy decisions"
echo "  - llm_outputs/preview/ - Generated content (if phase 3 was run)"
echo
echo "To run the full workflow (all phases), use:"
echo "  python main.py <repo> <goal> <service> <materials> --multi-agent --auto-confirm" 