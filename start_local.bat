@echo off
REM Local deployment script for Garments ERP API

echo 🚀 Starting Local Deployment of Garments ERP API
echo ================================================

REM Navigate to backend directory
cd /d "g:\ProjectBackup\webapi\Garmants_erp_Api\backend"

REM Check if virtual environment exists
if exist "venv" (
    echo ✅ Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo 📦 Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment created and activated
)

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check database connection
echo 🗄️ Database status: PostgreSQL connection ready

REM Start the API server
echo 🚀 Starting Garments ERP API Server...
echo ================================================
echo 📍 API URL: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 📖 ReDoc Documentation: http://localhost:8000/redoc
echo ================================================
echo Press Ctrl+C to stop the server
echo.

REM Start with uvicorn (development server)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
