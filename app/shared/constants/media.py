"""
Media-related constants for file uploads and management.
Centralizes all media handling configuration and validation rules.
"""

class MediaConstants:
    """Media handling and validation constants"""
    
    # Media types
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_VIDEO = "video"
    DEFAULT_MEDIA_TYPE = MEDIA_TYPE_IMAGE
    
    VALID_MEDIA_TYPES = [MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO]
    
    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "gif"]
    SUPPORTED_VIDEO_FORMATS = ["mp4", "mov", "avi", "webm"]
    
    # File size limits (in MB)
    MAX_IMAGE_SIZE_MB = 10
    MAX_VIDEO_SIZE_MB = 100
    MIN_FILE_SIZE_BYTES = 1024  # 1KB minimum
    
    # Image dimensions
    MAX_IMAGE_WIDTH = 4000
    MAX_IMAGE_HEIGHT = 4000
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    
    # Recommended dimensions
    HERO_IMAGE_WIDTH = 1080
    HERO_IMAGE_HEIGHT = 1080
    THUMBNAIL_WIDTH = 300
    THUMBNAIL_HEIGHT = 300
    
    # Video constraints
    MAX_VIDEO_DURATION_SECONDS = 300  # 5 minutes
    MIN_VIDEO_DURATION_SECONDS = 1
    
    # Cloudinary settings
    DEFAULT_FOLDER = "contestlet"
    HERO_FOLDER = "contest-heroes"
    GENERAL_FOLDER = "general"
    
    # Folder validation
    MIN_FOLDER_NAME_LENGTH = 3
    MAX_FOLDER_NAME_LENGTH = 50
    
    # Image quality and optimization
    IMAGE_QUALITY = "auto"
    IMAGE_FORMAT = "auto"
    VIDEO_QUALITY = "auto"
    
    # Transformations
    HERO_TRANSFORMATION = "c_fill,w_1080,h_1080,q_auto,f_auto"
    THUMBNAIL_TRANSFORMATION = "c_fill,w_300,h_300,q_auto,f_auto"
    
    # Upload settings
    MAX_CONCURRENT_UPLOADS = 5
    UPLOAD_TIMEOUT_SECONDS = 60
    RETRY_ATTEMPTS = 3
    
    # MIME types
    IMAGE_MIME_TYPES = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif"
    }
    
    VIDEO_MIME_TYPES = {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "webm": "video/webm"
    }
    
    # Storage paths
    CONTEST_HERO_PATH = "contests/{contest_id}/hero"
    GENERAL_UPLOAD_PATH = "uploads/{user_id}/{timestamp}"
    
    # CDN settings
    CDN_BASE_URL = "https://res.cloudinary.com"
    SECURE_DELIVERY = True
    
    # Metadata
    MAX_METADATA_SIZE = 1024  # 1KB
    ALLOWED_METADATA_FIELDS = ["title", "description", "alt_text", "tags"]


class MediaMessages:
    """Standardized media-related messages"""
    
    # Upload messages
    UPLOAD_SUCCESS = "Media uploaded successfully"
    UPLOAD_FAILED = "Media upload failed"
    UPLOAD_IN_PROGRESS = "Upload in progress"
    UPLOAD_TIMEOUT = "Upload timed out"
    
    # Validation messages
    INVALID_FILE_FORMAT = "Invalid file format"
    INVALID_IMAGE_FORMAT = "Invalid image format"
    INVALID_VIDEO_FORMAT = "Invalid video format"
    FILE_TOO_LARGE = "File size exceeds maximum limit"
    FILE_TOO_SMALL = "File size below minimum requirement"
    INVALID_DIMENSIONS = "Invalid image dimensions"
    INVALID_DURATION = "Invalid video duration"
    INVALID_FOLDER_NAME = "Invalid folder name"
    
    # Deletion messages
    DELETION_SUCCESS = "Media deleted successfully"
    DELETION_FAILED = "Media deletion failed"
    MEDIA_NOT_FOUND = "Media not found"
    DELETION_NOT_ALLOWED = "Media deletion not allowed"
    
    # Retrieval messages
    MEDIA_INFO_RETRIEVED = "Media information retrieved successfully"
    MEDIA_LIST_RETRIEVED = "Media list retrieved successfully"
    MEDIA_NOT_ACCESSIBLE = "Media not accessible"
    
    # Service messages
    SERVICE_HEALTHY = "Media service is healthy"
    SERVICE_UNAVAILABLE = "Media service is unavailable"
    CLOUDINARY_ERROR = "Cloudinary service error"
    CONFIGURATION_ERROR = "Media service configuration error"
    
    # Permission messages
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions for media operation"
    CONTEST_ACCESS_DENIED = "Contest media access denied"
    MEDIA_OWNERSHIP_REQUIRED = "Media ownership required for this operation"
    
    # Processing messages
    PROCESSING_COMPLETE = "Media processing completed"
    PROCESSING_FAILED = "Media processing failed"
    OPTIMIZATION_APPLIED = "Media optimization applied"


class MediaErrors:
    """Media-specific error codes"""
    
    # Upload errors
    UPLOAD_FAILED = "UPLOAD_FAILED"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_TOO_SMALL = "FILE_TOO_SMALL"
    UPLOAD_TIMEOUT = "UPLOAD_TIMEOUT"
    
    # Validation errors
    INVALID_DIMENSIONS = "INVALID_DIMENSIONS"
    INVALID_DURATION = "INVALID_DURATION"
    INVALID_MIME_TYPE = "INVALID_MIME_TYPE"
    INVALID_FOLDER_NAME = "INVALID_FOLDER_NAME"
    
    # Service errors
    CLOUDINARY_ERROR = "CLOUDINARY_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # Access errors
    MEDIA_NOT_FOUND = "MEDIA_NOT_FOUND"
    ACCESS_DENIED = "ACCESS_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Processing errors
    PROCESSING_FAILED = "PROCESSING_FAILED"
    OPTIMIZATION_FAILED = "OPTIMIZATION_FAILED"
    TRANSFORMATION_FAILED = "TRANSFORMATION_FAILED"


class MediaDefaults:
    """Default values for media operations"""
    
    DEFAULT_IMAGE_QUALITY = 80
    DEFAULT_VIDEO_QUALITY = 70
    DEFAULT_COMPRESSION = True
    DEFAULT_AUTO_FORMAT = True
    
    # Default transformations
    DEFAULT_HERO_SIZE = "1080x1080"
    DEFAULT_THUMBNAIL_SIZE = "300x300"
    DEFAULT_PREVIEW_SIZE = "600x400"
    
    # Default folders by context
    CONTEST_FOLDER = "contests"
    USER_FOLDER = "users"
    ADMIN_FOLDER = "admin"
    TEMP_FOLDER = "temp"
    
    # Default metadata
    DEFAULT_ALT_TEXT = "Contest media"
    DEFAULT_TITLE = "Untitled media"
    
    # Default expiration
    TEMP_FILE_EXPIRY_HOURS = 24
    CACHE_EXPIRY_HOURS = 168  # 1 week
