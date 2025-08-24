import logging
import phonenumbers
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class TwilioVerifyService:
    """
    Service for handling OTP verification using Twilio Verify API.
    Provides secure phone verification without storing OTP codes locally.
    """
    
    def __init__(self):
        self.client = None
        self.verify_service_sid = None
        
        try:
            self.use_mock = settings.USE_MOCK_SMS
            self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            # Always try to import twilio, but handle gracefully
            try:
                from twilio.rest import Client
                self.twilio_available = True
            except ImportError:
                logger.warning("Twilio library not available, using mock mode")
                self.twilio_available = False
                self.use_mock = True
            
            # If not using mock and twilio is available, initialize client
            if not self.use_mock and self.twilio_available:
                try:
                    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                        logger.error("Twilio credentials not configured, falling back to mock")
                        self.use_mock = True
                    elif not self.verify_service_sid:
                        logger.error("TWILIO_VERIFY_SERVICE_SID not configured, falling back to mock")
                        self.use_mock = True
                    else:
                        from twilio.rest import Client
                        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                        logger.info("Twilio client initialized successfully")
                        
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio client: {e}")
                    self.use_mock = True
            
            # Log final configuration
            mode = "MOCK" if self.use_mock else "REAL"
            logger.info(f"TwilioVerifyService initialized in {mode} mode")
            
        except Exception as e:
            logger.error(f"Critical error in TwilioVerifyService init: {e}")
            # Fall back to safe defaults
            self.use_mock = True
            self.twilio_available = False
            self.client = None
            self.verify_service_sid = None

    def validate_phone_number(self, phone: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate and format phone number using phonenumbers library.
        In mock mode (development), allows test numbers.
        
        Returns:
            Tuple of (is_valid, formatted_phone, error_message)
        """
        try:
            # In mock mode, allow test numbers
            if self.use_mock:
                # Allow common test phone number patterns
                test_patterns = [
                    "+15551234567", "+15559876543", "+15551111111", 
                    "+15552222222", "+15553333333", "+15554444444",
                    "+18187958204"  # Admin number
                ]
                
                if phone in test_patterns:
                    logger.info(f"MOCK MODE: Accepting test phone number {self._mask_phone(phone)}")
                    return True, phone, None
            
            # Parse the phone number
            parsed = phonenumbers.parse(phone, "US")  # Default to US region
            
            # Check if it's a valid number
            if not phonenumbers.is_valid_number(parsed):
                return False, phone, "Invalid phone number"
            
            # Check if it's a US number (optional requirement)
            if phonenumbers.region_code_for_number(parsed) != "US":
                return False, phone, "Only US phone numbers are supported"
            
            # Format in E.164 format
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted, None
            
        except phonenumbers.NumberParseException as e:
            return False, phone, f"Phone number parse error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error validating phone {phone}: {e}")
            return False, phone, "Phone number validation failed"

    async def send_verification(self, phone: str) -> Tuple[bool, str]:
        """
        Send OTP verification code using Twilio Verify API.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate phone number first
            is_valid, formatted_phone, error = self.validate_phone_number(phone)
            if not is_valid:
                logger.warning(f"Phone validation failed for {phone}: {error}")
                return False, error or "Invalid phone number"
            
            if self.use_mock:
                return await self._send_mock_verification(formatted_phone)
            else:
                return await self._send_twilio_verification(formatted_phone)
                
        except Exception as e:
            logger.error(f"Unexpected error in send_verification: {e}")
            return False, "Failed to send verification code. Please try again."

    async def check_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        Verify OTP code using Twilio Verify API.
        
        Returns:
            Tuple of (success, message)
        """
        # Validate phone number first
        is_valid, formatted_phone, error = self.validate_phone_number(phone)
        if not is_valid:
            return False, error or "Invalid phone number"
        
        if self.use_mock:
            return await self._check_mock_verification(formatted_phone, code)
        else:
            return await self._check_twilio_verification(formatted_phone, code)

    async def _send_mock_verification(self, phone: str) -> Tuple[bool, str]:
        """Mock verification sending - just log the action"""
        masked_phone = self._mask_phone(phone)
        logger.info(f"MOCK VERIFICATION to {masked_phone}: Use code '123456'")
        print(f"🔐 MOCK VERIFICATION to {masked_phone}: Use code '123456' for testing")
        return True, "Verification code sent (mock)"

    async def _send_twilio_verification(self, phone: str) -> Tuple[bool, str]:
        """Send verification using Twilio Verify API"""
        try:
            verification = self.client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(
                to=phone,
                channel='sms'
            )
            
            masked_phone = self._mask_phone(phone)
            logger.info(f"Verification sent to {masked_phone}, status: {verification.status}")
            
            if verification.status == 'pending':
                return True, "Verification code sent successfully"
            else:
                return False, f"Failed to send verification: {verification.status}"
                
        except Exception as e:
            logger.error(f"Twilio Verify send error for {self._mask_phone(phone)}: {e}")
            
            # Handle specific Twilio errors
            error_message = str(e)
            if "rate limit" in error_message.lower():
                return False, "Too many requests. Please wait before requesting another code."
            elif "invalid" in error_message.lower() and "phone" in error_message.lower():
                return False, "Invalid phone number format."
            elif "blocked" in error_message.lower():
                return False, "This phone number is blocked from receiving messages."
            else:
                return False, "Failed to send verification code. Please try again."

    async def _check_mock_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """Mock verification checking - always accept '123456'"""
        masked_phone = self._mask_phone(phone)
        
        if code == "123456":
            logger.info(f"MOCK VERIFICATION SUCCESS for {masked_phone}")
            return True, "Verification successful (mock)"
        else:
            logger.info(f"MOCK VERIFICATION FAILED for {masked_phone}: wrong code {code}")
            return False, "Invalid verification code (mock)"

    async def _check_twilio_verification(self, phone: str, code: str) -> Tuple[bool, str]:
        """Check verification using Twilio Verify API"""
        try:
            verification_check = self.client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(
                to=phone,
                code=code
            )
            
            masked_phone = self._mask_phone(phone)
            logger.info(f"Verification check for {masked_phone}, status: {verification_check.status}")
            
            if verification_check.status == 'approved':
                return True, "Verification successful"
            elif verification_check.status == 'pending':
                return False, "Invalid or expired verification code"
            else:
                return False, f"Verification failed: {verification_check.status}"
                
        except Exception as e:
            logger.error(f"Twilio Verify check error for {self._mask_phone(phone)}: {e}")
            
            # Handle specific Twilio errors
            error_message = str(e)
            if "expired" in error_message.lower():
                return False, "Verification code has expired. Please request a new one."
            elif "invalid" in error_message.lower():
                return False, "Invalid verification code."
            elif "rate limit" in error_message.lower():
                return False, "Too many verification attempts. Please wait before trying again."
            else:
                return False, "Verification failed. Please try again."

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging (security)"""
        if len(phone) > 4:
            return phone[:-4] + "****"
        return "****"


# Global Twilio Verify service instance
twilio_verify_service = TwilioVerifyService()
