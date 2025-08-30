# Garments ERP API - Production Deployment Guide

## 🚀 Quick Start

Your Garments ERP API is ready for production deployment! Here are the available options:

### 1. Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t garments-erp-api .
docker run -p 8000:8000 garments-erp-api
```

### 2. Cloud Deployment
- **Heroku**: One-click deployment ready
- **Railway**: Simple git-based deployment
- **DigitalOcean**: App Platform deployment
- **AWS**: ECS/Elastic Beanstalk ready

### 3. Local Production
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production server)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 📋 Features Deployed

✅ **Sales Bills System**: Complete with financial transactions
✅ **Bill Book Management**: Tax types and numbering
✅ **Customer & Agent Management**: Full CRM features
✅ **Product Management**: Variants, stock, pricing
✅ **Purchase Management**: Orders, returns, payments
✅ **Financial Integration**: Ledger transactions, accounting
✅ **Authentication**: JWT token-based security
✅ **API Documentation**: Auto-generated Swagger/OpenAPI docs

## 🔧 Configuration

### Environment Variables
Set these in your deployment environment:
```
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENVIRONMENT=production
```

### Database
PostgreSQL with all required tables and enums automatically created on startup.

## 📚 API Documentation

Once deployed, access your API documentation at:
- **Swagger UI**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`

## 🛡️ Security Features

- JWT token authentication
- CORS middleware configured
- SQL injection protection via SQLAlchemy ORM
- Input validation with Pydantic schemas
- Rate limiting ready (uncomment in production)

## 📊 Performance

- Async FastAPI framework
- Connection pooling
- Background task processing
- Optimized database queries with proper indexing

## 🔍 Monitoring

Health check endpoint available at `/` for monitoring services.

## 📞 Support

For deployment issues, check the logs and ensure all environment variables are properly set.
