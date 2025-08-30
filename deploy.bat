@echo off
REM Windows deployment script for Garments ERP API

echo 🚀 Starting Garments ERP API Production Deployment
echo =================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop with Compose.
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "ssl" mkdir ssl

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 🔧 Creating .env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://postgres:postgres123@db:5432/garments_erp
        echo.
        echo # Security Keys ^(CHANGE THESE IN PRODUCTION!^)
        echo SECRET_KEY=change-this-super-secret-key-in-production
        echo JWT_SECRET_KEY=change-this-jwt-secret-key-in-production
        echo.
        echo # Environment
        echo ENVIRONMENT=production
        echo DEBUG=false
        echo.
        echo # Rate Limiting
        echo RATE_LIMIT_ENABLED=true
        echo RATE_LIMIT_PER_MINUTE=60
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
    ) > .env
    echo ✅ .env file created. Please review and update the configuration.
) else (
    echo ✅ .env file already exists.
)

REM Build and start services
echo 🏗️ Building Docker images...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

REM Wait for services
echo ⏳ Waiting for services to start...
timeout /t 15 /nobreak > nul

REM Check API health
echo 🔍 Checking API health...
curl -f http://localhost:8000/ > nul 2>&1
if errorlevel 1 (
    echo ⏳ API is still starting up. This may take a few more moments...
    timeout /t 10 /nobreak > nul
    curl -f http://localhost:8000/ > nul 2>&1
    if errorlevel 1 (
        echo ❌ API failed to start. Check logs with: docker-compose logs api
        pause
        exit /b 1
    )
)

echo.
echo 🎉 Deployment completed successfully!
echo =================================================
echo 📍 API URL: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 📖 ReDoc Documentation: http://localhost:8000/redoc
echo 🗄️ Database: PostgreSQL on localhost:5432
echo.
echo 🔧 Management Commands:
echo   View logs: docker-compose logs -f api
echo   Stop services: docker-compose down
echo   Restart: docker-compose restart
echo   Update: docker-compose pull ^&^& docker-compose up -d
echo.
echo ⚠️  Production Notes:
echo   1. Update the SECRET_KEY and JWT_SECRET_KEY in .env
echo   2. Configure your domain in nginx.conf
echo   3. Add SSL certificates in ./ssl/ directory
echo   4. Set up proper backup for PostgreSQL data
echo.
echo 🚀 Your Garments ERP API is now running!
echo.
pause
