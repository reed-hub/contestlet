"""
Clean media service for file upload and management.
Handles Cloudinary integration and media operations.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.contest import Contest
from app.shared.exceptions.base import (
    BusinessException, 
    ValidationException,
    ErrorCode
)


class MediaService:
    """
    Clean media service with centralized business logic.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_contest_hero(
        self,
        contest_id: int,
        file,
        media_type: str = "image",
        user_id: int = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Upload hero image/video for contest.
        
        Args:
            contest_id: Contest ID
            file: UploadFile object from FastAPI
            media_type: Type of media (image/video)
            user_id: ID of user uploading
            user_role: Role of user uploading
            
        Returns:
            Upload result with URLs and metadata
        """
        try:
            # Validate contest exists
            contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
            if not contest:
                raise BusinessException(
                    message=f"Contest with ID {contest_id} not found",
                    error_code=ErrorCode.CONTEST_NOT_FOUND,
                    details={"contest_id": contest_id}
                )
            
            # Read file data
            file_data = await file.read()
            filename = file.filename or "unknown"
            
            # TODO: Implement Cloudinary upload
            # For now, return a mock response that matches MediaUploadData schema
            from datetime import datetime
            
            result = {
                "public_id": f"contest_{contest_id}_{filename}",
                "secure_url": f"https://example.com/media/{contest_id}/{filename}",
                "format": filename.split('.')[-1] if '.' in filename else "jpg",
                "resource_type": media_type,
                "bytes": len(file_data),
                "width": 1080 if media_type == "image" else None,
                "height": 1080 if media_type == "image" else None,
                "duration": 30.0 if media_type == "video" else None,
                "created_at": datetime.now(),
                "folder": f"contests/{contest_id}",
                "version": 1
            }
            
            # Update contest with media info
            contest.image_url = result["secure_url"]
            contest.image_public_id = result["public_id"]
            contest.media_type = media_type
            contest.media_metadata = {
                "filename": filename,
                "size": len(file_data),
                "format": result["format"],
                "uploaded_by": user_id,
                "uploaded_at": result["created_at"].isoformat()
            }
            
            self.db.commit()
            
            return result
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, BusinessException):
                raise
            raise BusinessException(
                message=f"Failed to upload media: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                details={"error": str(e)}
            )
    
    async def delete_contest_hero(
        self,
        contest_id: int,
        user_id: int = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Delete hero media for contest.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            Deletion result
        """
        try:
            # Validate contest exists
            contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
            if not contest:
                raise BusinessException(
                    message=f"Contest with ID {contest_id} not found",
                    error_code=ErrorCode.CONTEST_NOT_FOUND,
                    details={"contest_id": contest_id}
                )
            
            # Store the public_id before deletion
            deleted_public_id = contest.image_public_id or f"contest_{contest_id}"
            
            # TODO: Implement Cloudinary deletion
            # For now, just clear the database fields
            contest.image_url = None
            contest.image_public_id = None
            contest.media_type = None
            contest.media_metadata = None
            
            self.db.commit()
            
            # Return format matching MediaDeletionData schema
            from datetime import datetime
            return {
                "public_id": deleted_public_id,
                "deleted_at": datetime.now(),
                "result": "success"
            }
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, BusinessException):
                raise
            raise BusinessException(
                message=f"Failed to delete media: {str(e)}",
                error_code=ErrorCode.DATABASE_ERROR,
                details={"error": str(e)}
            )
    
    async def get_contest_hero_info(
        self,
        contest_id: int,
        user_id: int = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Get contest hero media information.
        
        Args:
            contest_id: Contest ID
            user_id: ID of user requesting
            user_role: Role of user requesting
            
        Returns:
            Media information
        """
        try:
            contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
            if not contest:
                raise BusinessException(
                    message=f"Contest with ID {contest_id} not found",
                    error_code=ErrorCode.CONTEST_NOT_FOUND,
                    details={"contest_id": contest_id}
                )
            
            # Return format matching MediaInfoData schema
            if not contest.image_url:
                raise BusinessException(
                    message=f"No media found for contest {contest_id}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"contest_id": contest_id}
                )
            
            # Parse metadata if available
            metadata = contest.media_metadata or {}
            
            return {
                "public_id": contest.image_public_id or f"contest_{contest_id}",
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
            
        except Exception as e:
            if isinstance(e, BusinessException):
                raise
            raise BusinessException(
                message=f"Failed to get media info: {str(e)}",
                error_code=ErrorCode.DATABASE_ERROR,
                details={"error": str(e)}
            )
    
    async def get_contest_media_list(
        self,
        contest_id: int,
        media_type: Optional[str] = None,
        user_id: int = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Get list of media for contest.
        
        Args:
            contest_id: Contest ID
            media_type: Filter by media type
            user_id: ID of user requesting
            user_role: Role of user requesting
            
        Returns:
            List of media items
        """
        try:
            contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
            if not contest:
                raise BusinessException(
                    message=f"Contest with ID {contest_id} not found",
                    error_code=ErrorCode.CONTEST_NOT_FOUND,
                    details={"contest_id": contest_id}
                )
            
            # For now, return the hero media if it exists
            media_list = []
            if contest.image_url:
                if not media_type or contest.media_type == media_type:
                    media_list.append({
                        "contest_id": contest_id,
                        "image_url": contest.image_url,
                        "public_id": contest.image_public_id,
                        "media_type": contest.media_type,
                        "metadata": contest.media_metadata
                    })
            
            return {
                "contest_id": contest_id,
                "media_items": media_list,
                "total_count": len(media_list)
            }
            
        except Exception as e:
            if isinstance(e, BusinessException):
                raise
            raise BusinessException(
                message=f"Failed to get media list: {str(e)}",
                error_code=ErrorCode.DATABASE_ERROR,
                details={"error": str(e)}
            )
    
    async def upload_direct_media(
        self,
        file,
        folder: str,
        media_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Upload media directly to Cloudinary.
        
        Args:
            file: UploadFile object
            folder: Cloudinary folder
            media_type: Type of media
            user_id: ID of user uploading
            
        Returns:
            Upload result
        """
        try:
            # Read file data
            file_data = await file.read()
            filename = file.filename or "unknown"
            
            # TODO: Implement Cloudinary upload
            # For now, return a mock response that matches MediaUploadData schema
            from datetime import datetime
            
            result = {
                "public_id": f"{folder}_{filename}",
                "secure_url": f"https://example.com/media/{folder}/{filename}",
                "format": filename.split('.')[-1] if '.' in filename else "jpg",
                "resource_type": media_type,
                "bytes": len(file_data),
                "width": 1080 if media_type == "image" else None,
                "height": 1080 if media_type == "image" else None,
                "duration": 30.0 if media_type == "video" else None,
                "created_at": datetime.now(),
                "folder": folder,
                "version": 1
            }
            
            return result
            
        except Exception as e:
            raise BusinessException(
                message=f"Failed to upload media: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                details={"error": str(e)}
            )
    
    async def check_service_health(self) -> Dict[str, Any]:
        """
        Check media service health and configuration.
        
        Returns:
            Health status information
        """
        try:
            # TODO: Add actual Cloudinary health check
            # For now, return a mock healthy status
            return {
                "healthy": True,
                "cloudinary_configured": False,  # Set to False since it's not implemented yet
                "status": "mock_mode",
                "message": "Media service is running in mock mode (Cloudinary not configured)",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "status": "error",
                "message": "Media service health check failed"
            }
