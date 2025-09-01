"""
Media-specific response models with type safety.
Provides standardized responses for all media endpoints.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse


class MediaUploadData(BaseModel):
    """Media upload result data"""
    public_id: str = Field(..., description="Cloudinary public ID")
    secure_url: str = Field(..., description="Secure HTTPS URL")
    format: str = Field(..., description="File format")
    resource_type: str = Field(..., description="Resource type (image/video)")
    bytes: int = Field(..., description="File size in bytes")
    width: Optional[int] = Field(None, description="Image/video width")
    height: Optional[int] = Field(None, description="Image/video height")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    created_at: datetime = Field(..., description="Upload timestamp")
    folder: str = Field(..., description="Cloudinary folder")
    version: int = Field(..., description="Version number")


class MediaUploadResponse(APIResponse[MediaUploadData]):
    """Type-safe response for media uploads"""
    pass


class MediaDeletionData(BaseModel):
    """Media deletion result data"""
    public_id: str = Field(..., description="Deleted media public ID")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    result: str = Field(..., description="Deletion result status")


class MediaDeletionResponse(APIResponse[MediaDeletionData]):
    """Type-safe response for media deletion"""
    pass


class MediaInfoData(BaseModel):
    """Media information data"""
    public_id: str = Field(..., description="Cloudinary public ID")
    secure_url: str = Field(..., description="Secure HTTPS URL")
    format: str = Field(..., description="File format")
    resource_type: str = Field(..., description="Resource type")
    bytes: int = Field(..., description="File size in bytes")
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    folder: str = Field(..., description="Cloudinary folder")
    tags: List[str] = Field(default_factory=list, description="Media tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MediaInfoResponse(APIResponse[MediaInfoData]):
    """Type-safe response for media information"""
    pass


class MediaListData(BaseModel):
    """Media list data"""
    media_items: List[MediaInfoData] = Field(..., description="List of media items")
    total_count: int = Field(..., description="Total number of media items")
    folder: str = Field(..., description="Folder path")
    contest_id: Optional[int] = Field(None, description="Associated contest ID")


class MediaListResponse(APIResponse[MediaListData]):
    """Type-safe response for media lists"""
    pass


class MediaHealthData(BaseModel):
    """Media service health data"""
    healthy: bool = Field(..., description="Service health status")
    cloudinary_configured: bool = Field(..., description="Cloudinary configuration status")
    upload_enabled: bool = Field(..., description="Upload functionality status")
    storage_available: bool = Field(..., description="Storage availability")
    last_check: datetime = Field(..., description="Last health check timestamp")
    version: str = Field(..., description="Service version")
    errors: List[str] = Field(default_factory=list, description="Health check errors")


class MediaHealthResponse(APIResponse[MediaHealthData]):
    """Type-safe response for media service health"""
    pass


class MediaTransformationData(BaseModel):
    """Media transformation result data"""
    original_url: str = Field(..., description="Original media URL")
    transformed_url: str = Field(..., description="Transformed media URL")
    transformation: str = Field(..., description="Applied transformation")
    format: str = Field(..., description="Output format")
    quality: str = Field(..., description="Applied quality setting")


class MediaTransformationResponse(APIResponse[MediaTransformationData]):
    """Type-safe response for media transformations"""
    pass


class MediaBulkOperationData(BaseModel):
    """Bulk media operation result data"""
    total_processed: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Processing errors")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Individual results")


class MediaBulkOperationResponse(APIResponse[MediaBulkOperationData]):
    """Type-safe response for bulk media operations"""
    pass
