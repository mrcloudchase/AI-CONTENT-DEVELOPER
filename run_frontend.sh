#!/bin/bash

# Run the Streamlit frontend for AI Content Developer

echo "🚀 Starting AI Content Developer Frontend..."
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable is not set"
    echo "   Please set it before running: export OPENAI_API_KEY='your-key'"
    echo ""
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: Streamlit is not installed"
    echo "   Run: pip install streamlit"
    exit 1
fi

# Set Python path to include project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run streamlit
echo "📝 Opening AI Content Developer in your browser..."
echo "   If it doesn't open automatically, visit: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run frontend/app.py 