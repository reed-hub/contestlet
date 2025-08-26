from fastapi import HTTPException, status
from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for consistent error handling"""
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_IN_USE = "RESOURCE_IN_USE"
    
    # Business logic errors
    CONTEST_NOT_ACTIVE = "CONTEST_NOT_ACTIVE"
    ENTRY_LIMIT_EXCEEDED = "ENTRY_LIMIT_EXCEEDED"
    INVALID_ENTRY = "INVALID_ENTRY"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class ContestletException(HTTPException):
    """Base exception for Contestlet application with standardized error format"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code.value,
                "message": message,
                "details": self.details
            }
        )


class AuthenticationError(ContestletException):
    """Authentication-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(ContestletException):
    """Authorization-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationError(ContestletException):
    """Validation-related errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if field:
            details = details or {}
            details["field"] = field
        
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ResourceNotFoundError(ContestletException):
    """Resource not found errors"""
    
    def __init__(self, resource_type: str, resource_id: Any, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with id {resource_id} not found"
        details = details or {}
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class RateLimitError(ContestletException):
    """Rate limiting errors"""
    
    def __init__(self, retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        message = "Rate limit exceeded. Please try again later."
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class BusinessLogicError(ContestletException):
    """Business logic validation errors"""
    
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


# Convenience functions for common errors
def raise_authentication_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise authentication error"""
    raise AuthenticationError(message, details)


def raise_authorization_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise authorization error"""
    raise AuthorizationError(message, details)


def raise_validation_error(message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Raise validation error"""
    raise ValidationError(message, field, details)


def raise_resource_not_found(resource_type: str, resource_id: Any, details: Optional[Dict[str, Any]] = None):
    """Raise resource not found error"""
    raise ResourceNotFoundError(resource_type, resource_id, details)


def raise_rate_limit_error(retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
    """Raise rate limit error"""
    raise RateLimitError(retry_after, details)


def raise_business_logic_error(error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
    """Raise business logic error"""
    raise BusinessLogicError(error_code, message, details)
