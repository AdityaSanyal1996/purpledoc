#!/bin/bash

# --- Configuration ---



echo "========================================"
echo "   🚀 Starting PurpleDoc Backend"
echo "========================================"



echo "✅ Server running at: http://127.0.0.1:8000"
echo "📝 API Docs available at: http://127.0.0.1:8000/docs"
echo "Press CTRL+C to stop."
echo "----------------------------------------"

# Run the server
python -m uvicorn purple.server:app --reload --port 8000