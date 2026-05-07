#!/bin/bash

# Graph Approach Backend Run Script
# Run this script to start the graph-based migration backend

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to repo root to ensure imports work
cd "$REPO_ROOT"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"

# Check for Azure OpenAI credentials
if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo "Warning: AZURE_OPENAI_API_KEY not set"
    echo "Migration functionality will not work without credentials"
fi

if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
    echo "Warning: AZURE_OPENAI_ENDPOINT not set"
fi

# Run the backend
echo "Starting Graph Approach Backend on port 5002..."
python "$SCRIPT_DIR/app.py"

