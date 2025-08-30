#!/bin/bash

# Production deployment script for Garments ERP API

set -e

echo "🚀 Starting Garments ERP API Production Deployment"
echo "================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs uploads ssl

# Set environment variables
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres123@db:5432/garments_erp

# Security Keys (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Environment
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_TITLE="Garments ERP API"
API_VERSION="1.0.0"

# CORS Origins (update with your frontend domains)
CORS_ORIGINS=["http://localhost:3000","https://your-frontend-domain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO

# Email Configuration (optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# Redis Configuration (optional)
# REDIS_URL=redis://redis:6379/0
EOF
    echo "✅ .env file created. Please review and update the configuration."
else
    echo "✅ .env file already exists."
fi

# Build and start services
echo "🏗️ Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if API is responding
echo "🔍 Checking API health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - API not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ API failed to start. Check logs with: docker-compose logs api"
    exit 1
fi

# Show status
echo ""
echo "🎉 Deployment completed successfully!"
echo "================================================="
echo "📍 API URL: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc Documentation: http://localhost:8000/redoc"
echo "🗄️ Database: PostgreSQL on localhost:5432"
echo ""
echo "🔧 Management Commands:"
echo "  View logs: docker-compose logs -f api"
echo "  Stop services: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Update: docker-compose pull && docker-compose up -d"
echo ""
echo "⚠️  Production Notes:"
echo "  1. Update the SECRET_KEY and JWT_SECRET_KEY in .env"
echo "  2. Configure your domain in nginx.conf"
echo "  3. Add SSL certificates in ./ssl/ directory"
echo "  4. Update CORS_ORIGINS with your frontend domains"
echo "  5. Set up proper backup for PostgreSQL data"
echo ""
echo "🚀 Your Garments ERP API is now running!"
