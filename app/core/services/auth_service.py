"""
Clean authentication service.
Centralizes all authentication logic with proper error handling.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.auth import jwt_manager
from app.shared.exceptions.base import AuthenticationException, ErrorCode
from app.shared.constants.auth import AuthMessages


class AuthService:
    """
    Clean authentication service with centralized token handling.
    """
    
    def __init__(self, user_repo, db: Session):
        self.user_repo = user_repo
        self.db = db
    
    async def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user from JWT token with proper error handling.
        
        Args:
            token: JWT token string
            
        Returns:
            User object if token is valid, None otherwise
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            # Verify token
            payload = jwt_manager.verify_token(token, "access")
            if not payload:
                raise AuthenticationException(
                    error_code=ErrorCode.TOKEN_INVALID,
                    message=AuthMessages.TOKEN_INVALID
                )
            
            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException(
                    error_code=ErrorCode.TOKEN_INVALID,
                    message=AuthMessages.MISSING_USER_ID
                )
            
            # Get user from database
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                raise AuthenticationException(
                    error_code=ErrorCode.INVALID_CREDENTIALS,
                    message=AuthMessages.ACCOUNT_NOT_FOUND
                )
            
            # Check if user is verified
            if not user.is_verified:
                raise AuthenticationException(
                    error_code=ErrorCode.ACCOUNT_NOT_VERIFIED,
                    message=AuthMessages.ACCOUNT_NOT_VERIFIED
                )
            
            return user
            
        except AuthenticationException:
            # Re-raise authentication exceptions
            raise
        except Exception as e:
            # Convert any other exception to authentication error
            raise AuthenticationException(
                error_code=ErrorCode.TOKEN_INVALID,
                message=AuthMessages.INVALID_CREDENTIALS
            ) from e
    
    async def validate_user_permissions(self, user: User, required_role: str) -> bool:
        """
        Validate if user has required role permissions.
        
        Args:
            user: User object
            required_role: Required role string
            
        Returns:
            True if user has required permissions
        """
        from app.shared.constants.auth import AuthConstants
        
        user_level = AuthConstants.ROLE_HIERARCHY.get(user.role, 0)
        required_level = AuthConstants.ROLE_HIERARCHY.get(required_role, 999)
        
        return user_level >= required_level
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID with proper error handling.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
