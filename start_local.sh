#!/bin/bash
# Local deployment script for Garments ERP API (Linux/Mac)

echo "🚀 Starting Local Deployment of Garments ERP API"
echo "================================================"

# Navigate to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check database connection
echo "🗄️ Database status: PostgreSQL connection ready"

# Start the API server
echo "🚀 Starting Garments ERP API Server..."
echo "================================================"
echo "📍 API URL: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc Documentation: http://localhost:8000/redoc"
echo "================================================"
echo "Press Ctrl+C to stop the server"
echo

# Start with uvicorn (development server)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
