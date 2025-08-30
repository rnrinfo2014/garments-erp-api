from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from routes import router
from seed import init_database

# Import settings if available
try:
    from config.settings import settings
    TITLE = settings.API_TITLE
    VERSION = settings.API_VERSION
    DESCRIPTION = settings.API_DESCRIPTION
    CORS_ORIGINS = settings.CORS_ORIGINS
except ImportError:
    # Fallback to environment variables or defaults
    TITLE = os.getenv("API_TITLE", "Garments ERP API")
    VERSION = os.getenv("API_VERSION", "1.0.0")
    DESCRIPTION = """
    Complete Garments ERP System with Sales Bills, Purchase Management, 
    Financial Transactions, and Comprehensive Business Logic.
    
    🔥 **Features:**
    - **Sales Bills System**: Complete with tax calculations and financial integration
    - **Bill Book Management**: Multiple bill books with different tax types
    - **Financial Transactions**: Automatic ledger updates and accounting
    - **Advanced Search**: Powerful filtering and search capabilities
    """
    CORS_ORIGINS = ["*"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    try:
        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    yield
    print("Shutting down...")

app = FastAPI(
    title=TITLE, 
    version=VERSION, 
    lifespan=lifespan,
    description=DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)


@app.get("/")
def read_root():
    return {
        "message": "Garments ERP API is running!", 
        "version": VERSION,
        "status": "healthy",
        "features": [
            "Sales Bills Management",
            "Purchase Order System", 
            "Financial Transactions",
            "Customer & Agent Management",
            "Product Management",
            "Bill Book System",
            "JWT Authentication"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "garments-erp-api"}


# Register routes
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
