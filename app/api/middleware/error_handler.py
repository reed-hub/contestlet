"""
Global error handling middleware for structured API responses.
Converts exceptions to standardized JSON responses.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from app.shared.exceptions.base import (
    ResourceNotFoundException,
    ValidationException, 
    BusinessException,
    ErrorCode
)
from app.shared.constants.http import HTTPStatusCodes, APIMessages

logger = logging.getLogger(__name__)


def convert_exception_to_response(exception: Exception) -> Dict[str, Any]:
    """
    Convert any exception to a standardized API response format.
    
    Args:
        exception: The exception to convert
        
    Returns:
        Dictionary with standardized error response format
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Handle structured exceptions
    if isinstance(exception, ResourceNotFoundException):
        return {
            "success": False,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details,
            "timestamp": timestamp,
            "status_code": HTTPStatusCodes.NOT_FOUND
        }
    
    elif isinstance(exception, ValidationException):
        return {
            "success": False,
            "error_code": exception.error_code,
            "message": exception.message,
            "errors": {
                "field_errors": exception.field_errors,
                "validation_errors": exception.validation_errors
            },
            "timestamp": timestamp,
            "status_code": HTTPStatusCodes.UNPROCESSABLE_ENTITY
        }
    
    elif isinstance(exception, BusinessException):
        # Map business exception codes to HTTP status codes
        status_code_map = {
            ErrorCode.UNAUTHORIZED: HTTPStatusCodes.UNAUTHORIZED,
            ErrorCode.FORBIDDEN: HTTPStatusCodes.FORBIDDEN,
            ErrorCode.CONTEST_PROTECTED: HTTPStatusCodes.CONFLICT,
            ErrorCode.BUSINESS_RULE_VIOLATION: HTTPStatusCodes.CONFLICT,
            ErrorCode.RATE_LIMIT_EXCEEDED: HTTPStatusCodes.TOO_MANY_REQUESTS
        }
        
        status_code = status_code_map.get(exception.error_code, HTTPStatusCodes.BAD_REQUEST)
        
        return {
            "success": False,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details,
            "timestamp": timestamp,
            "status_code": status_code
        }
    
    # Handle standard HTTP exceptions (FastAPI HTTPException)
    elif hasattr(exception, 'status_code') and hasattr(exception, 'detail'):
        return {
            "success": False,
            "error_code": "HTTP_ERROR",
            "message": str(exception.detail),
            "details": {"status_code": exception.status_code},
            "timestamp": timestamp,
            "status_code": exception.status_code
        }
    
    # Handle validation errors (Pydantic ValidationError)
    elif hasattr(exception, 'errors') and callable(getattr(exception, 'errors')):
        try:
            validation_errors = exception.errors()
            field_errors = {}
            
            for error in validation_errors:
                field_path = '.'.join(str(loc) for loc in error.get('loc', []))
                field_errors[field_path] = error.get('msg', 'Validation error')
            
            return {
                "success": False,
                "error_code": ErrorCode.VALIDATION_FAILED,
                "message": APIMessages.VALIDATION_FAILED,
                "errors": {
                    "field_errors": field_errors,
                    "validation_errors": validation_errors
                },
                "timestamp": timestamp,
                "status_code": HTTPStatusCodes.UNPROCESSABLE_ENTITY
            }
        except Exception:
            # Fallback if we can't parse validation errors
            pass
    
    # Handle generic exceptions
    else:
        # Log the full exception for debugging
        logger.error(f"Unhandled exception: {type(exception).__name__}: {str(exception)}", 
                    exc_info=True)
        
        return {
            "success": False,
            "error_code": ErrorCode.INTERNAL_ERROR,
            "message": APIMessages.INTERNAL_SERVER_ERROR,
            "details": {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception)
            } if logger.isEnabledFor(logging.DEBUG) else None,
            "timestamp": timestamp,
            "status_code": HTTPStatusCodes.INTERNAL_SERVER_ERROR
        }


class ErrorHandlingMiddleware:
    """
    FastAPI middleware for global error handling.
    Catches all unhandled exceptions and converts them to structured responses.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Convert exception to structured response
            error_response = convert_exception_to_response(exc)
            status_code = error_response.pop("status_code", HTTPStatusCodes.INTERNAL_SERVER_ERROR)
            
            # Send error response
            response = {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"access-control-allow-origin", b"*"],
                    [b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"],
                    [b"access-control-allow-headers", b"*"],
                ]
            }
            await send(response)
            
            import json
            body = json.dumps(error_response).encode()
            await send({
                "type": "http.response.body",
                "body": body
            })


def setup_error_handlers(app):
    """
    Setup error handlers for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", exc.status_code)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", exc.status_code)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", HTTPStatusCodes.UNPROCESSABLE_ENTITY)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @app.exception_handler(ResourceNotFoundException)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundException):
        """Handle resource not found exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", HTTPStatusCodes.NOT_FOUND)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """Handle business rule exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", HTTPStatusCodes.BAD_REQUEST)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        error_response = convert_exception_to_response(exc)
        status_code = error_response.pop("status_code", HTTPStatusCodes.INTERNAL_SERVER_ERROR)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )