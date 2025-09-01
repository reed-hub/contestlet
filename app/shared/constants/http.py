"""
HTTP-related constants for API responses and pagination.
Centralizes all HTTP status codes, headers, and API configuration.
"""

class HTTPStatusCodes:
    """Standard HTTP status codes"""
    
    # Success codes
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Redirection codes
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304
    
    # Client error codes
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server error codes
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class HTTPHeaders:
    """Standard HTTP headers"""
    
    # Authentication
    AUTHORIZATION = "Authorization"
    WWW_AUTHENTICATE = "WWW-Authenticate"
    
    # Content
    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"
    CONTENT_ENCODING = "Content-Encoding"
    
    # CORS
    ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
    ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
    ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
    ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
    
    # Caching
    CACHE_CONTROL = "Cache-Control"
    ETAG = "ETag"
    EXPIRES = "Expires"
    LAST_MODIFIED = "Last-Modified"
    
    # Rate limiting
    X_RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
    X_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    X_RATE_LIMIT_RESET = "X-RateLimit-Reset"
    
    # Request tracking
    X_REQUEST_ID = "X-Request-ID"
    X_CORRELATION_ID = "X-Correlation-ID"


class ContentTypes:
    """Standard content types"""
    
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    APPLICATION_FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSV = "text/csv"
    
    # Images
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    
    # Videos
    VIDEO_MP4 = "video/mp4"
    VIDEO_WEBM = "video/webm"
    VIDEO_QUICKTIME = "video/quicktime"


class APIConstants:
    """API-specific constants"""
    
    # Pagination defaults
    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 50
    MIN_PAGE_SIZE = 1
    MAX_PAGE_SIZE = 1000
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100
    DEFAULT_RATE_WINDOW = 3600  # 1 hour in seconds
    
    # Request limits
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Timeout settings
    DEFAULT_TIMEOUT = 30  # seconds
    LONG_TIMEOUT = 300  # 5 minutes for uploads
    
    # API versioning
    DEFAULT_API_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1"]
    
    # Response formats
    DEFAULT_RESPONSE_FORMAT = "json"
    SUPPORTED_FORMATS = ["json", "xml"]
    
    # Search and filtering
    MAX_SEARCH_LENGTH = 500
    MIN_SEARCH_LENGTH = 2
    DEFAULT_SEARCH_LIMIT = 100
    
    # Sorting
    DEFAULT_SORT_ORDER = "desc"
    VALID_SORT_ORDERS = ["asc", "desc"]
    
    # Cache settings
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    LONG_CACHE_TTL = 3600  # 1 hour
    SHORT_CACHE_TTL = 60  # 1 minute


class APIMessages:
    """Standard API response messages"""
    
    # Success messages
    SUCCESS = "Operation completed successfully"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    
    # Error messages
    BAD_REQUEST = "Invalid request data"
    UNAUTHORIZED = "Authentication required"
    FORBIDDEN = "Access denied"
    NOT_FOUND = "Resource not found"
    METHOD_NOT_ALLOWED = "Method not allowed"
    CONFLICT = "Resource conflict"
    UNPROCESSABLE_ENTITY = "Validation failed"
    TOO_MANY_REQUESTS = "Rate limit exceeded"
    INTERNAL_SERVER_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    
    # Validation messages
    VALIDATION_FAILED = "Input validation failed"
    REQUIRED_FIELD = "This field is required"
    INVALID_FORMAT = "Invalid format"
    VALUE_TOO_LONG = "Value exceeds maximum length"
    VALUE_TOO_SHORT = "Value below minimum length"
    
    # Authentication messages
    INVALID_TOKEN = "Invalid or expired token"
    TOKEN_REQUIRED = "Authentication token required"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
    
    # Pagination messages
    INVALID_PAGE = "Invalid page number"
    INVALID_PAGE_SIZE = "Invalid page size"
    NO_MORE_PAGES = "No more pages available"


class CORSSettings:
    """CORS configuration constants"""
    
    # Allowed origins (should be configured per environment)
    ALLOWED_ORIGINS = ["*"]  # Default - should be restricted in production
    
    # Allowed methods
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # Allowed headers
    ALLOWED_HEADERS = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID"
    ]
    
    # Exposed headers
    EXPOSED_HEADERS = [
        "X-Total-Count",
        "X-Page-Count", 
        "X-Rate-Limit-Limit",
        "X-Rate-Limit-Remaining",
        "X-Rate-Limit-Reset"
    ]
    
    # Credentials
    ALLOW_CREDENTIALS = True
    
    # Max age for preflight requests
    MAX_AGE = 86400  # 24 hours


class ResponseFormats:
    """Standard response format templates"""
    
    SUCCESS_RESPONSE = {
        "success": True,
        "data": None,
        "message": None,
        "timestamp": None
    }
    
    ERROR_RESPONSE = {
        "success": False,
        "error_code": None,
        "message": None,
        "details": None,
        "timestamp": None
    }
    
    PAGINATED_RESPONSE = {
        "success": True,
        "data": {
            "items": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "size": 50,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        },
        "message": None,
        "timestamp": None
    }


class SecurityHeaders:
    """Security-related HTTP headers"""
    
    # Content Security Policy
    CONTENT_SECURITY_POLICY = "Content-Security-Policy"
    CSP_DEFAULT = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    # XSS Protection
    X_XSS_PROTECTION = "X-XSS-Protection"
    XSS_PROTECTION_VALUE = "1; mode=block"
    
    # Content Type Options
    X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
    CONTENT_TYPE_OPTIONS_VALUE = "nosniff"
    
    # Frame Options
    X_FRAME_OPTIONS = "X-Frame-Options"
    FRAME_OPTIONS_VALUE = "DENY"
    
    # HSTS
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
    HSTS_VALUE = "max-age=31536000; includeSubDomains"
    
    # Referrer Policy
    REFERRER_POLICY = "Referrer-Policy"
    REFERRER_POLICY_VALUE = "strict-origin-when-cross-origin"