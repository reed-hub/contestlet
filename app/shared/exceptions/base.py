"""
Centralized exception handling system.
Provides consistent error responses and business logic exceptions.
"""

from enum import Enum
from typing import Optional, Dict, Any, Union
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Standardized error codes for consistent error handling"""
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_MISSING = "TOKEN_MISSING"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # Contest-specific errors
    CONTEST_NOT_FOUND = "CONTEST_NOT_FOUND"
    CONTEST_NOT_ACTIVE = "CONTEST_NOT_ACTIVE"
    CONTEST_PROTECTED = "CONTEST_PROTECTED"
    CONTEST_ENDED = "CONTEST_ENDED"
    CONTEST_NOT_STARTED = "CONTEST_NOT_STARTED"
    CONTEST_CANCELLED = "CONTEST_CANCELLED"
    
    # Entry errors
    ENTRY_LIMIT_EXCEEDED = "ENTRY_LIMIT_EXCEEDED"
    ENTRY_DUPLICATE = "ENTRY_DUPLICATE"
    ENTRY_NOT_ALLOWED = "ENTRY_NOT_ALLOWED"
    
    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    FIELD_VALUE_INVALID = "FIELD_VALUE_INVALID"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"


class BusinessException(Exception):
    """
    Base business logic exception with structured error information.
    Provides consistent error handling across the application.
    """
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.headers = headers or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "success": False,
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details
            }
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict(),
            headers=self.headers
        )


class AuthenticationException(BusinessException):
    """Authentication-related exceptions"""
    
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(BusinessException):
    """Authorization-related exceptions"""
    
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(BusinessException):
    """Resource not found exceptions"""
    
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: Optional[Union[int, str]] = None,
        message: Optional[str] = None
    ):
        if not message:
            if resource_id:
                message = f"{resource_type} with ID {resource_id} not found"
            else:
                message = f"{resource_type} not found"
        
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationException(BusinessException):
    """Validation-related exceptions"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        validation_details = details or {}
        if field_errors:
            validation_details["field_errors"] = field_errors
        
        super().__init__(
            error_code=ErrorCode.VALIDATION_FAILED,
            message=message,
            details=validation_details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ContestException(BusinessException):
    """Contest-specific business logic exceptions"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        contest_id: Optional[int] = None,
        contest_status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        contest_details = details or {}
        if contest_id:
            contest_details["contest_id"] = contest_id
        if contest_status:
            contest_details["contest_status"] = contest_status
        
        super().__init__(
            error_code=error_code,
            message=message,
            details=contest_details
        )


class RateLimitException(BusinessException):
    """Rate limiting exceptions"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        rate_limit_details = details or {}
        if retry_after:
            rate_limit_details["retry_after"] = retry_after
        
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=rate_limit_details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers
        )


# Convenience functions for raising common exceptions
def raise_not_found(resource_type: str = "Resource", resource_id: Optional[Union[int, str]] = None):
    """Raise a resource not found exception"""
    raise ResourceNotFoundException(resource_type, resource_id)


def raise_validation_error(message: str, field_errors: Optional[Dict[str, str]] = None):
    """Raise a validation exception"""
    raise ValidationException(message, field_errors)


def raise_authentication_error(message: str = "Authentication failed"):
    """Raise an authentication exception"""
    raise AuthenticationException(message=message)


def raise_authorization_error(message: str = "Access denied"):
    """Raise an authorization exception"""
    raise AuthorizationException(message=message)


def raise_contest_error(
    error_code: ErrorCode,
    message: str,
    contest_id: Optional[int] = None,
    contest_status: Optional[str] = None
):
    """Raise a contest-specific exception"""
    raise ContestException(error_code, message, contest_id, contest_status)


def raise_rate_limit_error(message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
    """Raise a rate limit exception"""
    raise RateLimitException(message, retry_after)


# Legacy compatibility functions (to be removed after refactoring)
def raise_resource_not_found(message: str):
    """Legacy function - use raise_not_found instead"""
    raise ResourceNotFoundException(message=message)


def raise_business_logic_error(message: str):
    """Legacy function - use specific exception types instead"""
    raise BusinessException(ErrorCode.BUSINESS_RULE_VIOLATION, message)
