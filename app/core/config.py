from pydantic import Field, validator, computed_field
from pydantic_settings import BaseSettings
from typing import Optional, List, Set
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Main application settings with environment-specific configuration"""
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./contestlet.db",
        description="Database connection URL"
    )
    
    # Security
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=1440, description="JWT expiration in minutes")
    jwt_refresh_expire_minutes: int = Field(default=10080, description="JWT refresh expiration in minutes")
    
    # Twilio
    twilio_account_sid: Optional[str] = Field(default=None, description="Twilio Account SID")
    twilio_auth_token: Optional[str] = Field(default=None, description="Twilio Auth Token")
    twilio_phone_number: Optional[str] = Field(default=None, description="Twilio Phone Number")
    twilio_verify_service_sid: Optional[str] = Field(default=None, description="Twilio Verify Service SID")
    use_mock_sms: bool = Field(default=True, description="Use mock SMS for development")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=5, description="Max requests per window")
    rate_limit_window: int = Field(default=300, description="Rate limit window in seconds")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for rate limiting")
    
    # Admin
    admin_phones: str = Field(default="+18187958204", description="Comma-separated admin phone numbers")
    admin_token: str = Field(
        default="contestlet-admin-super-secret-token-change-in-production",
        description="Legacy admin token for backward compatibility"
    )
    
    # Cloudinary Configuration
    cloudinary_cloud_name: str = Field(default="", description="Cloudinary cloud name")
    cloudinary_api_key: str = Field(default="", description="Cloudinary API key")
    cloudinary_api_secret: str = Field(default="", description="Cloudinary API secret")
    cloudinary_folder: str = Field(default="contestlet", description="Base folder for media uploads")
    
    # CORS
    cors_origins: Optional[str] = Field(default=None, description="Comma-separated CORS origins")
    allow_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3002",
            "http://localhost:8000"
        ],
        description="Allowed CORS origins"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials")
    allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        description="Allowed HTTP methods"
    )
    allow_headers: List[str] = Field(
        default=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers"
        ], 
        description="Allowed headers"
    )
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_environments = {'development', 'staging', 'production'}
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    @validator('allow_origins', pre=True)
    def parse_cors_origins(cls, v, values):
        """Parse CORS origins from environment variable if provided"""
        cors_origins = values.get('cors_origins')
        if cors_origins:
            # Parse comma-separated string into list
            return [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
        return v
    
    @computed_field
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @computed_field
    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"
    
    @computed_field
    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url.lower()
    
    @computed_field
    @property
    def is_postgresql(self) -> bool:
        return "postgresql" in self.database_url.lower()
    
    @computed_field
    @property
    def connect_args(self) -> dict:
        """SQLite-specific connection arguments"""
        return {"check_same_thread": False} if self.is_sqlite else {}
    
    @computed_field
    @property
    def jwt_expire_delta(self) -> int:
        """JWT expiration in seconds"""
        return self.jwt_expire_minutes * 60
    
    @computed_field
    @property
    def is_twilio_configured(self) -> bool:
        """Check if Twilio is properly configured"""
        return all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_verify_service_sid])
    
    @computed_field
    @property
    def is_cloudinary_configured(self) -> bool:
        """Check if Cloudinary is properly configured"""
        return bool(
            self.cloudinary_cloud_name and
            self.cloudinary_api_key and
            self.cloudinary_api_secret
        )
    
    @computed_field
    @property
    def cloudinary_config(self) -> dict:
        """Get Cloudinary configuration dictionary"""
        return {
            "cloud_name": self.cloudinary_cloud_name,
            "api_key": self.cloudinary_api_key,
            "api_secret": self.cloudinary_api_secret,
            "secure": True
        }
    
    @computed_field
    @property
    def phone_set(self) -> Set[str]:
        """Get set of normalized admin phone numbers"""
        if not self.admin_phones:
            return set()
        return {phone.strip() for phone in self.admin_phones.split(',') if phone.strip()}
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Don't load settings at module level - let it be loaded when needed
# settings = get_settings()
