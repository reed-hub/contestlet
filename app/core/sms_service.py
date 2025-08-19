import random
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self.use_mock = settings.USE_MOCK_SMS
        if not self.use_mock:
            try:
                from twilio.rest import Client
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                self.from_phone = settings.TWILIO_PHONE_NUMBER
            except ImportError:
                logger.warning("Twilio not available, falling back to mock SMS")
                self.use_mock = True
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.use_mock = True

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP code"""
        return f"{random.randint(100000, 999999)}"

    async def send_otp(self, phone: str, code: str) -> bool:
        """Send OTP code via SMS"""
        message = f"Your Contestlet verification code is: {code}. Valid for 5 minutes."
        
        if self.use_mock:
            return await self._send_mock_sms(phone, message)
        else:
            return await self._send_twilio_sms(phone, message)

    async def _send_mock_sms(self, phone: str, message: str) -> bool:
        """Mock SMS sending - just log the message"""
        logger.info(f"MOCK SMS to {phone}: {message}")
        print(f"🔐 MOCK SMS to {phone}: {message}")
        return True

    async def _send_twilio_sms(self, phone: str, message: str) -> bool:
        """Send SMS via Twilio"""
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=phone
            )
            logger.info(f"SMS sent successfully to {phone}, SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False


# Global SMS service instance
sms_service = SMSService()
