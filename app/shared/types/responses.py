"""
Standardized response type definitions.
Provides type safety for all API responses.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# Generic type variable for response data
T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response wrapper for all endpoints.
    Ensures consistent response format across the application.
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data payload")
    message: Optional[str] = Field(None, description="Human-readable message")
    errors: Optional[Dict[str, Any]] = Field(None, description="Error details if any")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response for list endpoints.
    """
    items: List[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors"""
    success: bool = Field(False, description="Always false for errors")
    message: str = Field(..., description="General error message")
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(APIResponse[Dict[str, Any]]):
    """Simple success response without specific data type"""
    pass


class MessageResponse(BaseModel):
    """Simple message response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(..., description="Status of dependent services")


class BulkOperationResponse(BaseModel):
    """Response for bulk operations"""
    success: bool = Field(..., description="Overall operation success")
    total_processed: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: List[ErrorDetail] = Field(default_factory=list, description="Errors encountered")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Individual results")


class FileUploadResponse(BaseModel):
    """Response for file upload operations"""
    success: bool = Field(..., description="Upload success status")
    file_id: Optional[str] = Field(None, description="Uploaded file identifier")
    file_url: Optional[str] = Field(None, description="Public URL of uploaded file")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeletionResponse(BaseModel):
    """Response for resource deletion operations"""
    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Deletion confirmation message")
    resource_id: Union[int, str] = Field(..., description="ID of deleted resource")
    resource_type: str = Field(..., description="Type of deleted resource")
    deleted_at: datetime = Field(default_factory=datetime.utcnow)
    cleanup_summary: Optional[Dict[str, Any]] = Field(None, description="Cleanup operation summary")


class StatusUpdateResponse(BaseModel):
    """Response for status update operations"""
    success: bool = Field(..., description="Update success status")
    message: str = Field(..., description="Update confirmation message")
    old_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="New status")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[int] = Field(None, description="ID of user who made the update")


# Type aliases for common response patterns
ListResponse = APIResponse[PaginatedResponse[T]]
DetailResponse = APIResponse[T]
CreateResponse = APIResponse[T]
UpdateResponse = APIResponse[T]
