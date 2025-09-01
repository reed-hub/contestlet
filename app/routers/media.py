"""
Clean, refactored media management API endpoints.
Uses new clean architecture with service layer and proper error handling.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, Path
from typing import Optional

from app.services.media_service import MediaService
from app.core.dependencies.auth import get_admin_or_sponsor_user, get_current_user
from app.core.dependencies.services import get_media_service
from app.models.user import User
from app.shared.types.responses import APIResponse
from app.api.responses.media import (
    MediaUploadResponse,
    MediaDeletionResponse,
    MediaInfoResponse,
    MediaListResponse
)
from app.shared.constants.media import MediaConstants, MediaMessages
from app.shared.exceptions.base import ValidationException

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/contests/{contest_id}/hero", response_model=MediaUploadResponse)
async def upload_contest_hero(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    file: UploadFile = File(..., description="Hero image or video file"),
    media_type: str = Query(
        MediaConstants.DEFAULT_MEDIA_TYPE,
        regex=f"^({'|'.join(MediaConstants.VALID_MEDIA_TYPES)})$",
        description="Media type: image or video"
    ),
    current_user: User = Depends(get_admin_or_sponsor_user),
    media_service: MediaService = Depends(get_media_service)
) -> MediaUploadResponse:
    """
    Upload contest hero image or video.
    Clean controller with service delegation and proper validation.
    """
    # Validate file format
    if not file.filename:
        raise ValidationException(
            message=MediaMessages.INVALID_FILE_FORMAT,
            field_errors={"file": "Filename is required"}
        )
    
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if media_type == MediaConstants.MEDIA_TYPE_IMAGE:
        if file_extension not in MediaConstants.SUPPORTED_IMAGE_FORMATS:
            raise ValidationException(
                message=MediaMessages.INVALID_IMAGE_FORMAT,
                field_errors={"file": f"Supported formats: {MediaConstants.SUPPORTED_IMAGE_FORMATS}"}
            )
    elif media_type == MediaConstants.MEDIA_TYPE_VIDEO:
        if file_extension not in MediaConstants.SUPPORTED_VIDEO_FORMATS:
            raise ValidationException(
                message=MediaMessages.INVALID_VIDEO_FORMAT,
                field_errors={"file": f"Supported formats: {MediaConstants.SUPPORTED_VIDEO_FORMATS}"}
            )
    
    # Validate file size
    max_size = (MediaConstants.MAX_IMAGE_SIZE_MB if media_type == MediaConstants.MEDIA_TYPE_IMAGE 
                else MediaConstants.MAX_VIDEO_SIZE_MB) * 1024 * 1024
    
    if file.size and file.size > max_size:
        max_mb = MediaConstants.MAX_IMAGE_SIZE_MB if media_type == MediaConstants.MEDIA_TYPE_IMAGE else MediaConstants.MAX_VIDEO_SIZE_MB
        raise ValidationException(
            message=MediaMessages.FILE_TOO_LARGE,
            field_errors={"file": f"File size must be less than {max_mb}MB"}
        )
    
    upload_result = await media_service.upload_contest_hero(
        file=file,
        contest_id=contest_id,
        media_type=media_type
    )
    
    # Check if upload was successful
    if not upload_result.get("success", False):
        raise ValidationException(
            message=f"Media upload failed: {upload_result.get('error', 'Unknown error')}",
            field_errors={"file": "Upload to Cloudinary failed"}
        )
    
    # Update contest with the real Cloudinary URL
    from app.database.database import get_db
    from app.models.contest import Contest
    from datetime import datetime
    
    # Get database session and update contest
    db = next(get_db())
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    if contest:
        contest.image_url = upload_result["url"]  # Real Cloudinary URL!
        contest.image_public_id = upload_result["public_id"]
        contest.media_type = media_type
        contest.media_metadata = {
            "filename": file.filename,
            "size": upload_result["bytes"],
            "format": upload_result["format"],
            "uploaded_at": datetime.now().isoformat(),
            "width": upload_result.get("width"),
            "height": upload_result.get("height")
        }
        db.commit()
    
    # Convert original service response to MediaUploadData format
    media_data = {
        "public_id": upload_result["public_id"],
        "secure_url": upload_result["url"],  # Real Cloudinary URL!
        "format": upload_result["format"],
        "resource_type": upload_result["resource_type"],
        "bytes": upload_result["bytes"],
        "width": upload_result.get("width"),
        "height": upload_result.get("height"),
        "duration": None,  # TODO: Add duration for videos
        "created_at": datetime.now(),  # Use current time for now
        "folder": f"contests/{contest_id}",
        "version": 1  # Default version
    }
    
    return MediaUploadResponse(
        success=True,
        data=media_data,
        message=MediaMessages.UPLOAD_SUCCESS
    )


@router.delete("/contests/{contest_id}/hero", response_model=MediaDeletionResponse)
async def delete_contest_hero(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: User = Depends(get_admin_or_sponsor_user),
    media_service: MediaService = Depends(get_media_service)
) -> MediaDeletionResponse:
    """
    Delete contest hero media.
    Clean controller with proper authorization and error handling.
    """
    deletion_success = await media_service.delete_contest_hero(contest_id=contest_id)
    
    if not deletion_success:
        raise ValidationException(
            message="Failed to delete contest media",
            field_errors={"contest_id": "Media deletion failed"}
        )
    
    # Convert to MediaDeletionData format
    from datetime import datetime
    
    deletion_data = {
        "public_id": f"contestlet/contests/{contest_id}/hero",
        "deleted_at": datetime.now(),
        "result": "success"
    }
    
    return MediaDeletionResponse(
        success=True,
        data=deletion_data,
        message=MediaMessages.DELETION_SUCCESS
    )


@router.get("/contests/{contest_id}/hero", response_model=MediaInfoResponse)
async def get_contest_hero_info(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: Optional[User] = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
) -> MediaInfoResponse:
    """
    Get contest hero media information.
    Public endpoint with optional user context.
    """
    # The original service doesn't have get_contest_hero_info, so we'll query the database directly
    from app.database.database import get_db
    from app.models.contest import Contest
    from sqlalchemy.orm import Session
    
    # Get database session (this is a temporary workaround)
    db = next(get_db())
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    if not contest or not contest.image_url:
        raise ValidationException(
            message=f"No media found for contest {contest_id}",
            field_errors={"contest_id": "Contest has no media"}
        )
    
    # Parse metadata if available
    metadata = contest.media_metadata or {}
    
    media_info = {
        "public_id": contest.image_public_id or f"contestlet/contests/{contest_id}/hero",
        "secure_url": contest.image_url,
        "format": metadata.get("format", "jpg"),
        "resource_type": contest.media_type or "image",
        "bytes": metadata.get("size", 0),
        "width": 1080,
        "height": 1080,
        "duration": None,
        "created_at": metadata.get("uploaded_at", "2024-01-01T00:00:00Z"),
        "folder": f"contests/{contest_id}",
        "tags": [],
        "metadata": metadata
    }
    
    return MediaInfoResponse(
        success=True,
        data=media_info,
        message="Media information retrieved successfully"
    )


# Temporarily disabled - original service doesn't have this method
# @router.get("/contests/{contest_id}/media", response_model=MediaListResponse)
# async def get_contest_media_list(...)


# Temporarily disabled - original service doesn't have upload_direct_media method
# @router.post("/upload/direct", response_model=MediaUploadResponse)
# async def upload_direct_media(...)


# Temporarily disabled - original service doesn't have these methods
# @router.delete("/delete/{public_id}")
# async def delete_media_by_id(...)

# @router.get("/info/{public_id}", response_model=MediaInfoResponse)
# async def get_media_info(...)


@router.get("/health")
async def media_service_health(
    media_service: MediaService = Depends(get_media_service)
) -> APIResponse[dict]:
    """
    Check media service health and configuration.
    """
    # Check if Cloudinary is configured in the original service
    health_status = {
        "healthy": media_service.enabled,
        "cloudinary_configured": media_service.enabled,
        "status": "active" if media_service.enabled else "disabled",
        "message": "Cloudinary configured and ready" if media_service.enabled else "Cloudinary not configured",
        "base_folder": media_service.base_folder if media_service.enabled else None
    }
    
    return APIResponse(
        success=health_status["healthy"],
        data=health_status,
        message="Media service health check completed"
    )
