"""
Authentication and authorization constants.
Centralizes JWT, OTP, and security-related configuration.
"""

class AuthConstants:
    """Authentication configuration constants"""
    
    # JWT Configuration
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES = 10080  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days
    
    # Token types
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
    OTP_RETRY_AFTER_SECONDS = 300
    
    # OTP Configuration
    OTP_CODE_LENGTH = 6
    OTP_LENGTH = 6  # Alias for compatibility
    OTP_EXPIRY_MINUTES = 10
    OTP_EXPIRE_MINUTES = 10  # Alias for compatibility
    MAX_OTP_ATTEMPTS = 3
    
    # Phone validation
    MIN_PHONE_LENGTH = 10
    MAX_PHONE_LENGTH = 15
    
    # Default roles
    DEFAULT_USER_ROLE = "user"
    ADMIN_ROLE = "admin"
    SPONSOR_ROLE = "sponsor"
    USER_ROLE = "user"
    
    # Valid roles
    VALID_ROLES = [ADMIN_ROLE, SPONSOR_ROLE, USER_ROLE]
    
    # Role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        USER_ROLE: 1,
        SPONSOR_ROLE: 2,
        ADMIN_ROLE: 3
    }


class AuthMessages:
    """Authentication-related messages"""
    
    # Success messages
    OTP_SENT_SUCCESS = "OTP code sent successfully"
    PHONE_VERIFIED_SUCCESS = "Phone verified successfully"
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logout successful"
    
    # Error messages
    INVALID_CREDENTIALS = "Invalid authentication credentials"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Invalid token format"
    MISSING_TOKEN = "Authentication token required"
    MISSING_USER_ID = "Missing user ID in token"
    
    # OTP messages
    OTP_INVALID = "Invalid OTP code"
    OTP_EXPIRED = "OTP code has expired"
    OTP_TOO_MANY_ATTEMPTS = "Too many OTP attempts. Please request a new code."
    OTP_RATE_LIMITED = "Too many OTP requests. Please try again later."
    
    # Phone validation messages
    PHONE_INVALID_FORMAT = "Invalid phone number format"
    PHONE_VALIDATION_FAILED = "Phone number validation failed"
    PHONE_ALREADY_VERIFIED = "Phone number already verified"
    
    # Permission messages
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions for this action"
    ADMIN_ACCESS_REQUIRED = "Admin access required"
    SPONSOR_ACCESS_REQUIRED = "Sponsor access required"
    ROLE_UPGRADE_REQUIRED = "Role upgrade required for this action"
    
    # Account messages
    ACCOUNT_NOT_FOUND = "Account not found"
    ACCOUNT_DISABLED = "Account has been disabled"
    ACCOUNT_NOT_VERIFIED = "Account not verified"


class AuthErrors:
    """Authentication error codes"""
    
    # Token errors
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_MISSING = "TOKEN_MISSING"
    
    # Credential errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_OTP = "INVALID_OTP"
    INVALID_PHONE = "INVALID_PHONE"
    
    # Permission errors
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ROLE_REQUIRED = "ROLE_REQUIRED"
    
    # Rate limiting errors
    RATE_LIMITED = "RATE_LIMITED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    
    # Account errors
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ACCOUNT_NOT_VERIFIED = "ACCOUNT_NOT_VERIFIED"


class SecurityConstants:
    """Security-related constants"""
    
    # Password requirements (if implemented)
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Session management
    MAX_CONCURRENT_SESSIONS = 5
    SESSION_TIMEOUT_MINUTES = 30
    
    # API security
    MAX_REQUEST_SIZE_MB = 10
    MAX_REQUESTS_PER_MINUTE = 100
    
    # CORS settings
    DEFAULT_CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8000"
    ]
    
    ALLOWED_METHODS = [
        "GET", "POST", "PUT", "DELETE", 
        "OPTIONS", "PATCH", "HEAD"
    ]
    
    ALLOWED_HEADERS = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ]
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
