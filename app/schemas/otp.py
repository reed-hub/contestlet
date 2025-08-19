from pydantic import BaseModel, Field
from typing import Optional


class OTPRequest(BaseModel):
    phone: str = Field(..., description="Phone number to send OTP to")


class OTPVerification(BaseModel):
    phone: str = Field(..., description="Phone number")
    code: str = Field(..., description="OTP code to verify")


class OTPResponse(BaseModel):
    message: str
    retry_after: Optional[int] = Field(None, description="Seconds until next request allowed")


class OTPVerificationResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[int] = None
