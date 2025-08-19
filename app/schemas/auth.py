from pydantic import BaseModel, Field


class PhoneVerificationRequest(BaseModel):
    phone: str = Field(..., description="Phone number to verify")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
