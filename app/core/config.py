from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    DATABASE_URL: str = "sqlite:///./contestlet.db"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Twilio settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None  # Required for SMS notifications
    TWILIO_VERIFY_SERVICE_SID: Optional[str] = None
    USE_MOCK_SMS: bool = True  # Set to False to use real Twilio services
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 5  # Max OTP requests per window
    RATE_LIMIT_WINDOW: int = 300  # Window in seconds (5 minutes)
    
    # Redis settings (for rate limiting)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Admin settings
    ADMIN_TOKEN: str = "contestlet-admin-super-secret-token-change-in-production"  # Legacy support
    ADMIN_PHONES: str = "+18187958204"  # Comma-separated list of admin phone numbers
    
    def get_admin_phones(self) -> set:
        """Get set of normalized admin phone numbers"""
        if not self.ADMIN_PHONES:
            return set()
        
        admin_phones = set()
        for phone in self.ADMIN_PHONES.split(','):
            phone = phone.strip()
            if phone:
                admin_phones.add(phone)
        return admin_phones
    
    class Config:
        env_file = ".env"


settings = Settings()
