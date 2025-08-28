"""
Media Management API Endpoints

Handles image and video uploads for contests with Cloudinary integration.
Supports both admin and sponsor uploads with proper authentication.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.database.database import get_db
from app.core.dependencies import get_admin_user, get_sponsor_user, get_current_user
from app.models.user import User
from app.models.contest import Contest
from app.services.media_service import MediaService, get_media_service
from app.core.datetime_utils import utc_now
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])
security = HTTPBearer()


@router.post("/contests/{contest_id}/hero")
async def upload_contest_hero(
    contest_id: int,
    file: UploadFile = File(..., description="Hero image or video file"),
    media_type: str = Query("image", description="Media type: 'image' or 'video'"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Upload contest hero image or video
    
    - **Supports**: Images (JPEG, PNG, WebP, GIF) and Videos (MP4, MOV, AVI)
    - **Optimization**: Automatic compression and format conversion
    - **Size**: 1:1 aspect ratio (1080x1080) for consistency
    - **Storage**: Environment-specific Cloudinary folders
    - **Access**: Admin and sponsor users only
    """
    
    # Extract and validate JWT token
    from app.core.auth import jwt_manager
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = jwt_manager.verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_role = payload.get("role")
    user_id = int(payload.get("sub"))
    
    # Validate user role
    if user_role not in ["admin", "sponsor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and sponsor users can upload contest media"
        )
    
    # Validate media type
    if media_type not in ["image", "video"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media type must be 'image' or 'video'"
        )
    
    # Validate file type
    if not media_service.validate_file_type(file, media_type):
        allowed_types = {
            "image": ["JPEG", "PNG", "WebP", "GIF"],
            "video": ["MP4", "MOV", "AVI"]
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for {media_type}. Allowed: {allowed_types[media_type]}"
        )
    
    # Validate file size (50MB limit)
    if not media_service.validate_file_size(file, max_size_mb=50):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit"
        )
    
    # Check if contest exists and user has permission
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # For sponsors, ensure they own the contest
    if user_role == "sponsor" and contest.created_by_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload media for your own contests"
        )
    
    # Upload to Cloudinary
    upload_result = await media_service.upload_contest_hero(file, contest_id, media_type)
    
    if not upload_result["success"]:
        logger.error(f"Media upload failed for contest {contest_id}: {upload_result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {upload_result.get('error', 'Unknown error')}"
        )
    
    # Update contest record with media information
    contest.image_url = upload_result["url"]
    contest.image_public_id = upload_result["public_id"]
    contest.media_type = media_type
    contest.media_metadata = {
        "format": upload_result.get("format"),
        "width": upload_result.get("width"),
        "height": upload_result.get("height"),
        "bytes": upload_result.get("bytes"),
        "resource_type": upload_result.get("resource_type"),
        "uploaded_at": upload_result.get("created_at"),
        "uploaded_by": user_id
    }
    
    db.commit()
    db.refresh(contest)
    
    logger.info(f"Successfully uploaded {media_type} for contest {contest_id} by user {user_id}")
    
    # Generate optimized URLs for different use cases
    optimized_urls = {}
    if upload_result["public_id"]:
        optimized_urls = {
            "thumbnail": media_service.get_thumbnail_url(upload_result["public_id"]),
            "medium": media_service.get_medium_url(upload_result["public_id"]),
            "large": media_service.get_large_url(upload_result["public_id"])
        }
    
    return {
        "success": True,
        "message": f"Hero {media_type} uploaded successfully",
        "contest_id": contest_id,
        "media_type": media_type,
        "url": upload_result["url"],
        "public_id": upload_result["public_id"],
        "optimized_urls": optimized_urls,
        "metadata": {
            "format": upload_result.get("format"),
            "dimensions": f"{upload_result.get('width')}x{upload_result.get('height')}",
            "size_bytes": upload_result.get("bytes")
        }
    }


@router.delete("/contests/{contest_id}/hero")
async def delete_contest_hero(
    contest_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Delete contest hero media
    
    - **Removes**: Both image and video versions from Cloudinary
    - **Updates**: Contest record to remove media references
    - **Access**: Admin and sponsor users only
    """
    
    # Extract and validate JWT token
    from app.core.auth import jwt_manager
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = jwt_manager.verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_role = payload.get("role")
    user_id = int(payload.get("sub"))
    
    # Validate user role
    if user_role not in ["admin", "sponsor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and sponsor users can delete contest media"
        )
    
    # Check if contest exists and user has permission
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # For sponsors, ensure they own the contest
    if user_role == "sponsor" and contest.created_by_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete media from your own contests"
        )
    
    # Check if contest has media
    if not contest.image_url and not contest.image_public_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest has no hero media to delete"
        )
    
    # Delete from Cloudinary
    deletion_success = await media_service.delete_contest_hero(contest_id)
    
    if not deletion_success:
        logger.warning(f"Failed to delete media from Cloudinary for contest {contest_id}")
        # Continue with database cleanup even if Cloudinary deletion failed
    
    # Update contest record
    contest.image_url = None
    contest.image_public_id = None
    contest.media_type = "image"  # Reset to default
    contest.media_metadata = None
    
    db.commit()
    db.refresh(contest)
    
    logger.info(f"Successfully deleted media for contest {contest_id} by user {user_id}")
    
    return {
        "success": True,
        "message": "Hero media deleted successfully",
        "contest_id": contest_id
    }


@router.get("/contests/{contest_id}/hero/urls")
async def get_contest_hero_urls(
    contest_id: int,
    db: Session = Depends(get_db),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Get optimized URLs for contest hero media
    
    - **Public endpoint**: No authentication required
    - **Returns**: Various sizes and formats for responsive display
    - **Optimization**: WebP, AVIF auto-selection based on browser support
    """
    
    # Get contest
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if contest has media
    if not contest.image_public_id:
        return {
            "contest_id": contest_id,
            "has_media": False,
            "fallback_url": contest.image_url,  # Legacy URL if available
            "urls": {}
        }
    
    # Generate optimized URLs
    urls = {
        "original": contest.image_url,
        "thumbnail": media_service.get_thumbnail_url(contest.image_public_id),
        "small": media_service.get_optimized_url(contest.image_public_id, 200, 200),
        "medium": media_service.get_medium_url(contest.image_public_id),
        "large": media_service.get_large_url(contest.image_public_id),
        "extra_large": media_service.get_optimized_url(contest.image_public_id, 1200, 1200)
    }
    
    return {
        "contest_id": contest_id,
        "has_media": True,
        "media_type": contest.media_type,
        "urls": urls,
        "metadata": contest.media_metadata
    }


@router.get("/health")
async def media_service_health(
    media_service: MediaService = Depends(get_media_service)
):
    """
    Check media service health and configuration
    
    - **Public endpoint**: Service status information
    - **Configuration**: Shows if Cloudinary is properly configured
    """
    
    return {
        "service": "media",
        "status": "healthy" if media_service.enabled else "disabled",
        "cloudinary_configured": media_service.enabled,
        "environment": media_service.settings.environment,
        "base_folder": media_service.base_folder if media_service.enabled else None
    }
