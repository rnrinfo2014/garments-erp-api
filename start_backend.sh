#!/bin/bash
echo "🚀 Starting Garments ERP Backend Server..."
echo ""

# Activate virtual environment
source venv/Scripts/activate

# Start FastAPI server with auto-reload
echo "✅ Virtual environment activated"
echo "🌐 Starting FastAPI server on http://127.0.0.1:8000"
echo "📖 API Documentation will be available at http://127.0.0.1:8000/docs"
echo ""

uvicorn main:app --reload --host 127.0.0.1 --port 8000
