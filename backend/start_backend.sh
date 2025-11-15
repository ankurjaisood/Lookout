#!/bin/bash

echo "🔧 Starting Lookout Backend..."

# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "✅ Backend running on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
