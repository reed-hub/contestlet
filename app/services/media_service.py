"""
Media Management Service

Handles image and video uploads to Cloudinary with automatic optimization,
transformations, and environment-specific organization.
"""

import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any, Union
from fastapi import UploadFile, HTTPException, status
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class MediaService:
    """Service for managing media uploads and transformations via Cloudinary"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Configure Cloudinary if credentials are available
        if self.settings.is_cloudinary_configured:
            cloudinary.config(**self.settings.cloudinary_config)
            self.enabled = True
            logger.info(f"Cloudinary configured for environment: {self.settings.environment}")
        else:
            self.enabled = False
            logger.warning("Cloudinary not configured - media uploads will be disabled")
        
        # Use the cloudinary_folder directly as it already includes environment
        self.base_folder = self.settings.cloudinary_folder
    
    def _check_enabled(self):
        """Ensure Cloudinary is properly configured"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Media service not configured. Please configure Cloudinary credentials."
            )
    
    async def upload_contest_hero(
        self, 
        file: UploadFile, 
        contest_id: int,
        media_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Upload contest hero image or video to Cloudinary
        
        Args:
            file: The uploaded file
            contest_id: Contest ID for organization
            media_type: "image" or "video"
            
        Returns:
            Dictionary with upload results and URLs
        """
        self._check_enabled()
        
        # Generate unique public_id for this contest
        public_id = f"{self.base_folder}/contests/{contest_id}/hero"
        
        try:
            if media_type == "video":
                result = cloudinary.uploader.upload(
                    file.file,
                    public_id=public_id,
                    resource_type="video",
                    overwrite=True,
                    format="mp4",  # Standardize to MP4
                    quality="auto",
                    transformation=[
                        {
                            "width": 1080, 
                            "height": 1080, 
                            "crop": "fill",
                            "gravity": "center"
                        },
                        {"quality": "auto:good"},
                        {"fetch_format": "auto"}
                    ],
                    # Video-specific settings
                    video_codec="h264",
                    audio_codec="aac"
                )
            else:
                result = cloudinary.uploader.upload(
                    file.file,
                    public_id=public_id,
                    resource_type="image",
                    overwrite=True,
                    quality="auto",
                    transformation=[
                        {
                            "width": 1080, 
                            "height": 1080, 
                            "crop": "fill",
                            "gravity": "center"
                        },
                        {"quality": "auto:good"},
                        {"fetch_format": "auto"}  # Auto-select WebP, AVIF, etc.
                    ]
                )
            
            logger.info(f"Successfully uploaded {media_type} for contest {contest_id}")
            
            return {
                "success": True,
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "format": result["format"],
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result["bytes"],
                "resource_type": result["resource_type"],
                "created_at": result["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to upload {media_type} for contest {contest_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_contest_hero(self, contest_id: int) -> bool:
        """
        Delete contest hero media from Cloudinary
        
        Args:
            contest_id: Contest ID
            
        Returns:
            True if deletion was successful
        """
        self._check_enabled()
        
        public_id = f"{self.base_folder}/contests/{contest_id}/hero"
        
        try:
            # Try deleting both image and video versions
            # Cloudinary will ignore if the resource doesn't exist
            image_result = cloudinary.uploader.destroy(public_id, resource_type="image")
            video_result = cloudinary.uploader.destroy(public_id, resource_type="video")
            
            # Consider successful if either deletion succeeded or resource wasn't found
            success = (
                image_result.get("result") in ["ok", "not found"] or
                video_result.get("result") in ["ok", "not found"]
            )
            
            if success:
                logger.info(f"Successfully deleted media for contest {contest_id}")
            else:
                logger.warning(f"Failed to delete media for contest {contest_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting media for contest {contest_id}: {str(e)}")
            return False
    
    def get_optimized_url(
        self, 
        public_id: str, 
        width: int = 400, 
        height: int = 400,
        quality: str = "auto",
        format: str = "auto"
    ) -> str:
        """
        Generate optimized URL for different display sizes
        
        Args:
            public_id: Cloudinary public ID
            width: Desired width
            height: Desired height
            quality: Quality setting (auto, auto:good, auto:best, etc.)
            format: Format setting (auto, webp, jpg, etc.)
            
        Returns:
            Optimized Cloudinary URL
        """
        if not self.enabled:
            return ""
        
        try:
            return cloudinary.CloudinaryImage(public_id).build_url(
                width=width,
                height=height,
                crop="fill",
                gravity="center",
                quality=quality,
                fetch_format=format
            )
        except Exception as e:
            logger.error(f"Error generating optimized URL for {public_id}: {str(e)}")
            return ""
    
    def get_thumbnail_url(self, public_id: str) -> str:
        """Get thumbnail URL (150x150)"""
        return self.get_optimized_url(public_id, 150, 150)
    
    def get_medium_url(self, public_id: str) -> str:
        """Get medium URL (400x400)"""
        return self.get_optimized_url(public_id, 400, 400)
    
    def get_large_url(self, public_id: str) -> str:
        """Get large URL (800x800)"""
        return self.get_optimized_url(public_id, 800, 800)
    
    def validate_file_type(self, file: UploadFile, media_type: str) -> bool:
        """
        Validate uploaded file type
        
        Args:
            file: Uploaded file
            media_type: Expected media type ("image" or "video")
            
        Returns:
            True if file type is valid
        """
        if media_type == "image":
            allowed_types = [
                "image/jpeg", "image/jpg", "image/png", 
                "image/webp", "image/gif"
            ]
        elif media_type == "video":
            allowed_types = [
                "video/mp4", "video/mov", "video/avi", 
                "video/quicktime", "video/x-msvideo"
            ]
        else:
            return False
        
        return file.content_type in allowed_types
    
    def validate_file_size(self, file: UploadFile, max_size_mb: int = 50) -> bool:
        """
        Validate file size
        
        Args:
            file: Uploaded file
            max_size_mb: Maximum size in MB
            
        Returns:
            True if file size is acceptable
        """
        # Note: This is a basic check. For more accurate size checking,
        # you might want to read the file content
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Try to get file size if available
        if hasattr(file, 'size') and file.size:
            return file.size <= max_size_bytes
        
        # If size is not available, we'll let Cloudinary handle it
        return True


# Dependency for FastAPI
def get_media_service() -> MediaService:
    """FastAPI dependency to get MediaService instance"""
    return MediaService()
