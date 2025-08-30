"""
Production configuration for Garments ERP API
"""
import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/garments_erp")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Configuration
    API_TITLE: str = "Garments ERP API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = """
    Complete Garments ERP System with Sales Bills, Purchase Management, 
    Financial Transactions, and Comprehensive Business Logic.
    
    🔥 **New Features:**
    - **Sales Bills System**: Complete with tax calculations and financial integration
    - **Bill Book Management**: Multiple bill books with different tax types
    - **Financial Transactions**: Automatic ledger updates and accounting
    - **Advanced Search**: Powerful filtering and search capabilities
    """
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "https://your-frontend-domain.com"
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "False").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Redis (for caching)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

# Global settings instance
settings = Settings()
