# 🚀 Garments ERP API - Production Ready

A complete Enterprise Resource Planning (ERP) system for garments business with advanced sales bills management, financial transactions, and comprehensive business logic.

## ✨ Features

### 🧾 Sales Bills System
- **Complete Sales Management**: Create, update, track sales bills
- **Tax Calculations**: Support for INCLUDE_TAX, EXCLUDE_TAX, WITHOUT_TAX
- **Financial Integration**: Automatic ledger updates and accounting
- **Payment Tracking**: Partial and full payment support
- **Business Logic**: Discount calculations, tax handling, amount computations

### 📚 Bill Book Management
- **Multiple Bill Books**: Different tax types and numbering schemes
- **Customizable Formats**: Flexible bill numbering and formatting
- **Tax Type Configuration**: Per bill book tax handling

### 💼 Business Management
- **Customer Management**: Complete CRM with credit limits and terms
- **Agent Management**: Commission tracking and sales assignments
- **Product Management**: Variants, SKUs, stock management, pricing
- **Purchase Management**: Orders, returns, supplier payments
- **Financial Management**: Ledger transactions, account balances

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: User permissions and access control
- **Input Validation**: Comprehensive data validation with Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM protection

## 🚀 Quick Deployment

### Option 1: Docker (Recommended)
```bash
# Clone and deploy
git clone <your-repo>
cd backend

# Run deployment script
./deploy.sh    # Linux/Mac
deploy.bat     # Windows

# Access your API
open http://localhost:8000/docs
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-secret"

# Run with production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Option 3: Cloud Deployment
See [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) for:
- Heroku
- Railway
- DigitalOcean
- AWS
- Google Cloud

## 📊 API Endpoints

### 🔐 Authentication
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/refresh` - Refresh access token

### 🧾 Sales Bills
- `GET /api/sales-bills/` - List sales bills (with filtering)
- `POST /api/sales-bills/` - Create new sales bill
- `GET /api/sales-bills/{id}` - Get sales bill details
- `PUT /api/sales-bills/{id}` - Update sales bill
- `PATCH /api/sales-bills/{id}/status` - Update status
- `DELETE /api/sales-bills/{id}` - Delete sales bill
- `POST /api/sales-bills/{id}/payments` - Add payment
- `POST /api/sales-bills/calculate` - Calculate taxes and amounts

### 💼 Business Management
- `GET|POST /api/customers/` - Customer management
- `GET|POST /api/agents/` - Agent management
- `GET|POST /api/products/` - Product management
- `GET|POST /api/bill-books/` - Bill book management
- `GET|POST /api/accounts/` - Account management

### 💰 Financial
- `GET|POST /api/ledger-transactions/` - Ledger transactions
- `GET /api/accounts/balances` - Account balances
- `GET /api/reports/sales` - Sales reports

## 🗄️ Database Schema

### Core Tables
- `sales_bills` - Main sales bill records
- `sales_bill_items` - Individual line items
- `sales_bill_payments` - Payment tracking
- `customers` - Customer master data
- `agents` - Sales agent information
- `product_variants` - Product catalog
- `bill_books` - Bill book configurations

### Financial Tables
- `ledger_transactions` - All financial transactions
- `accounts_master` - Chart of accounts
- `account_balances` - Real-time balances

## 🧪 Testing

### API Testing
```bash
# Test deployment
python test_deployment.py

# Run comprehensive tests
python test_sales_bills_playwright.py
```

### Manual Testing
Visit `/docs` for interactive API documentation and testing.

## ⚙️ Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Optional
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=["https://your-frontend.com"]
```

### Database Setup
PostgreSQL database with automatic table creation and seeding on startup.

## 📈 Performance

- **Async FastAPI**: High-performance async framework
- **Connection Pooling**: Efficient database connections
- **Background Tasks**: Non-blocking financial processing
- **Optimized Queries**: Proper indexing and query optimization
- **Caching Ready**: Redis integration ready

## 🔧 Production Features

- **Health Checks**: `/health` endpoint for monitoring
- **Logging**: Structured logging with configurable levels
- **Error Handling**: Comprehensive error responses
- **Rate Limiting**: API rate limiting (configurable)
- **CORS**: Cross-origin resource sharing configured
- **Security Headers**: Production security headers
- **SSL Ready**: HTTPS/SSL termination support

## 📚 Documentation

- **API Docs**: Available at `/docs` (Swagger UI)
- **ReDoc**: Available at `/redoc` (Alternative documentation)
- **OpenAPI**: Machine-readable API specification at `/openapi.json`

## 🔄 Deployment Workflow

1. **Development**: Local development with hot reload
2. **Testing**: Automated API testing with Playwright
3. **Staging**: Docker-based staging environment
4. **Production**: Cloud deployment with monitoring

## 🛠️ Maintenance

### Logs
```bash
# Docker logs
docker-compose logs -f api

# Direct logs
tail -f logs/api.log
```

### Database Backup
```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup.sql
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

## 📞 Support

### Health Monitoring
- API health: `GET /health`
- Database connectivity: Automatic verification
- Service status: Docker health checks

### Troubleshooting
1. Check API logs: `docker-compose logs api`
2. Verify database connection: Check `DATABASE_URL`
3. Test endpoints: Use `/docs` for interactive testing
4. Run deployment tests: `python test_deployment.py`

## 🎯 Production Checklist

- [ ] Update `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure `DATABASE_URL` for production database
- [ ] Set appropriate `CORS_ORIGINS`
- [ ] Enable SSL/HTTPS
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Test all major endpoints
- [ ] Verify authentication flows
- [ ] Check sales bills creation and calculations

## 🚀 Your API is Ready!

Your Garments ERP API is production-ready with:
- ✅ Complete sales bills system
- ✅ Financial transaction processing
- ✅ Comprehensive business logic
- ✅ Security and authentication
- ✅ Production deployment configuration
- ✅ Monitoring and health checks

Access your API at: `http://your-domain.com/docs`
