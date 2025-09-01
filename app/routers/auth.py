"""
Clean, refactored authentication API endpoints.
Uses new clean architecture with proper error handling and constants.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import PhoneVerificationRequest, TokenResponse, UserMeResponse
from app.schemas.otp import OTPRequest, OTPVerification, OTPResponse, OTPVerificationResponse
from app.core.auth import create_access_token, create_user_token, verify_token
from app.core.twilio_verify_service import twilio_verify_service
from app.core.rate_limiter import rate_limiter
from app.core.config import get_settings
from app.core.dependencies.auth import get_current_user
from app.shared.exceptions.base import (
    RateLimitException, 
    AuthenticationException, 
    ValidationException,
    ErrorCode
)
from app.shared.constants.auth import AuthConstants, AuthMessages, AuthErrors
from app.shared.types.responses import APIResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/request-otp", response_model=APIResponse[OTPResponse])
async def request_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
) -> APIResponse[OTPResponse]:
    """
    Request OTP code for phone verification using Twilio Verify API.
    Uses centralized rate limiting and error handling.
    """
    # Check rate limiting with centralized constants
    rate_limit_key = f"otp_request:{otp_request.phone}"
    if not rate_limiter.is_allowed(rate_limit_key):
        remaining_time = rate_limiter.get_reset_time(rate_limit_key)
        retry_after = int(remaining_time - datetime.now().timestamp()) if remaining_time else AuthConstants.OTP_RETRY_AFTER_SECONDS
        
        raise RateLimitException(
            message=AuthMessages.OTP_RATE_LIMITED,
            retry_after=retry_after
        )
    
    # Send verification using Twilio Verify API
    success, message = await twilio_verify_service.send_verification(otp_request.phone)
    
    if not success:
        raise ValidationException(
            message=message or AuthMessages.PHONE_VALIDATION_FAILED,
            field_errors={"phone": message}
        )
    
    otp_response = OTPResponse(
        message=message or AuthMessages.OTP_SENT_SUCCESS,
        retry_after=None
    )
    
    return APIResponse(
        success=True,
        data=otp_response,
        message=AuthMessages.OTP_SENT_SUCCESS
    )


@router.post("/verify-otp", response_model=APIResponse[OTPVerificationResponse])
async def verify_otp(
    otp_verification: OTPVerification,
    db: Session = Depends(get_db)
) -> APIResponse[OTPVerificationResponse]:
    """
    Verify OTP code using Twilio Verify API and return JWT token on success.
    Uses structured error handling and centralized user creation logic.
    """
    # Check verification using Twilio Verify API
    success, message = await twilio_verify_service.check_verification(
        otp_verification.phone, 
        otp_verification.code
    )
    
    if not success:
        raise AuthenticationException(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message=message or AuthMessages.OTP_INVALID
        )
    
    # Validation successful - get the validated phone number
    is_valid, formatted_phone, error = twilio_verify_service.validate_phone_number(otp_verification.phone)
    if not is_valid:
        raise ValidationException(
            message=error or AuthMessages.PHONE_VALIDATION_FAILED,
            field_errors={"phone": error}
        )
    
    # Get or create user with the formatted phone number
    user = db.query(User).filter(User.phone == formatted_phone).first()
    if not user:
        # Create new user with default role using constants
        settings = get_settings()
        admin_phones = settings.phone_set
        default_role = AuthConstants.ADMIN_ROLE if formatted_phone in admin_phones else AuthConstants.DEFAULT_USER_ROLE
        
        user = User(
            phone=formatted_phone,
            role=default_role,
            is_verified=True  # Phone is verified through OTP
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update verification status for existing user
        if not user.is_verified:
            user.is_verified = True
            db.commit()
    
    # Create JWT token with user's actual role from database
    access_token = create_user_token(
        user_id=user.id,
        phone=user.phone,
        role=user.role
    )
    
    verification_response = OTPVerificationResponse(
        success=True,
        message=AuthMessages.PHONE_VERIFIED_SUCCESS,
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )
    
    return APIResponse(
        success=True,
        data=verification_response,
        message=AuthMessages.LOGIN_SUCCESS
    )


@router.post("/verify-phone", response_model=APIResponse[TokenResponse])
async def verify_phone(
    phone_data: PhoneVerificationRequest,
    db: Session = Depends(get_db)
) -> APIResponse[TokenResponse]:
    """
    Legacy phone verification endpoint.
    Maintained for backward compatibility with improved error handling.
    """
    # Validate phone number format
    is_valid, formatted_phone, error = twilio_verify_service.validate_phone_number(phone_data.phone)
    if not is_valid:
        raise ValidationException(
            message=AuthMessages.PHONE_INVALID_FORMAT,
            field_errors={"phone": error}
        )
    
    # Check if user exists and is verified
    user = db.query(User).filter(User.phone == formatted_phone).first()
    if not user or not user.is_verified:
        raise AuthenticationException(
            error_code=ErrorCode.ACCOUNT_NOT_FOUND,
            message=AuthMessages.ACCOUNT_NOT_FOUND
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "phone": user.phone})
    
    token_response = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )
    
    return APIResponse(
        success=True,
        data=token_response,
        message=AuthMessages.LOGIN_SUCCESS
    )


@router.get("/me", response_model=APIResponse[UserMeResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserMeResponse]:
    """
    Get current user information from JWT token.
    Uses clean authentication dependency with proper error handling.
    """
    user_response = UserMeResponse(
        user_id=current_user.id,
        phone=current_user.phone,
        role=current_user.role,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )
    
    return APIResponse(
        success=True,
        data=user_response,
        message="User information retrieved successfully"
    )


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    current_user: User = Depends(get_current_user)
) -> APIResponse[dict]:
    """
    Logout endpoint (token invalidation would be handled client-side).
    Provides consistent API response format.
    """
    return APIResponse(
        success=True,
        data={"user_id": current_user.id},
        message=AuthMessages.LOGOUT_SUCCESS
    )
