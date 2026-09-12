import logging
import re
from io import BytesIO
from typing import Optional
from datetime import datetime
from xml.sax.saxutils import escape

try:
    from twilio.rest import Client
except ImportError:
    Client = None

gTTS = None

from app.core.config import settings

logger = logging.getLogger("sentinel.notifications")


def normalize_indian_phone_number(phone_number: str) -> str:
    """Normalize common Indian input formats to E.164."""
    value = re.sub(r"[\s().\-]", "", str(phone_number).strip())
    if value.startswith("00"):
        value = "+" + value[2:]
    if value.startswith("+91"):
        local = value[3:]
    elif value.startswith("91") and len(value) == 12:
        local = value[2:]
    elif value.startswith("0") and len(value) == 11:
        local = value[1:]
    else:
        local = value
    if not re.fullmatch(r"[6-9]\d{9}", local):
        raise ValueError("Enter a valid Indian mobile number.")
    value = "+91" + local
    return value


def _placeholder(value: str, names: tuple[str, ...]) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized in names or normalized.startswith("your_")


def _mask_phone(phone_number: str) -> str:
    return f"{phone_number[:4]}******{phone_number[-4:]}"


class NotificationService:
    """Manages SMS, voice calls, and TTS notifications."""

    def __init__(self):
        self.twilio_client = None
        self.configuration_error = None
        configured_values = (
            str(settings.twilio_account_sid or "").strip(),
            str(settings.twilio_auth_token or "").strip(),
            str(settings.twilio_phone_number or "").strip(),
        )
        self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number = configured_values
        if settings.enable_sms_alerts and (
            _placeholder(self.twilio_account_sid, ("your_twilio_account_sid", "ac_placeholder"))
            or _placeholder(self.twilio_auth_token, ("your_twilio_auth_token", "auth_token"))
            or _placeholder(self.twilio_phone_number, ("+1234567890", "your_twilio_phone_number"))
            or not re.fullmatch(r"AC[0-9a-f]{32}", self.twilio_account_sid, re.IGNORECASE)
            or not re.fullmatch(r"\+[1-9]\d{7,14}", self.twilio_phone_number)
        ):
            self.configuration_error = "SMS provider is not configured on the server."
        if settings.enable_sms_alerts and Client is None:
            self.configuration_error = "Twilio SDK is not installed on the server."
        if Client and settings.enable_sms_alerts and not self.configuration_error:
            try:
                self.twilio_client = Client(
                    settings.twilio_account_sid,
                    settings.twilio_auth_token
                )
            except Exception as e:
                self.configuration_error = "Twilio client initialization failed"
                logger.exception("Twilio client initialization failed")

    def health(self) -> dict:
        """Return safe provider status without returning credentials."""
        credentials_present = all((self.twilio_account_sid, self.twilio_auth_token))
        sender_configured = bool(self.twilio_phone_number)
        return {
            "sms_provider": "twilio",
            "configured": not bool(self.configuration_error) and bool(self.twilio_client),
            "sender_configured": sender_configured,
            "credentials_present": credentials_present,
            "configuration_error": self.configuration_error,
        }

    async def send_sms(
        self,
        phone_number: str,
        message: str
    ) -> dict:
        """Send SMS and return provider status without exposing secrets."""
        try:
            normalized_phone = normalize_indian_phone_number(phone_number)
        except ValueError as exc:
            return {"status": "failed", "error_code": "INVALID_PHONE_NUMBER", "error": str(exc), "phone_number": phone_number}

        if not settings.enable_sms_alerts:
            return {"status": "failed", "error": "SMS alerts are disabled", "phone_number": normalized_phone}
        if settings.demo_mode:
            logger.warning("[ALERT] Demo mode enabled; real SMS blocked for %s", _mask_phone(normalized_phone))
            return {"status": "failed", "error_code": "SMS_DEMO_MODE_ENABLED", "error": "Real SMS is disabled while demo mode is enabled.", "phone_number": normalized_phone}
        if self.configuration_error or not self.twilio_client:
            return {"status": "failed", "error_code": "SMS_PROVIDER_NOT_CONFIGURED", "error": self.configuration_error or "SMS provider is unavailable", "phone_number": normalized_phone}

        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=normalized_phone
            )

            logger.info(
                "[ALERT] SMS accepted: recipient=%s provider_message_id=%s",
                _mask_phone(normalized_phone),
                message_obj.sid,
            )

            return {
                "status": "SMS_ACCEPTED",
                "message_sid": message_obj.sid,
                "phone_number": normalized_phone,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.exception("[ALERT ERROR] Twilio/API error for %s", _mask_phone(normalized_phone))

            return {
                "status": "failed",
                "error_code": getattr(e, "code", None) or "SMS_PROVIDER_REJECTED",
                "error": str(e),
                "phone_number": normalized_phone
            }

    async def stop_voice_call(self, call_sid: str) -> dict:
        """Explicitly stop an active provider call; UI dismissal never calls this."""
        if not self.twilio_client or not call_sid:
            return {"status": "not_available", "call_sid": call_sid}
        try:
            call = self.twilio_client.calls(call_sid).update(status="completed")
            return {"status": "stopped", "call_sid": call.sid}
        except Exception as exc:
            logger.exception("Failed to stop provider call")
            return {"status": "failed", "call_sid": call_sid, "error": str(exc)}

    async def send_voice_alert(
        self,
        phone_number: str,
        message: str,
        message_type: str = "normal"
    ) -> dict:
        """
        Initiate a voice call with TTS message.

        message_type:
        'normal'
        'emergency'
        'police'
        """

        try:
            normalized_phone = normalize_indian_phone_number(phone_number)
        except ValueError as exc:
            return {"status": "failed", "error": str(exc), "phone_number": phone_number}

        if not settings.enable_voice_calls:
            return {"status": "failed", "error": "Voice calls are disabled", "phone_number": normalized_phone}
        if self.configuration_error or not self.twilio_client:
            return {"status": "failed", "error": self.configuration_error or "Twilio client is unavailable", "phone_number": normalized_phone}

        try:
            # Safely escape message for XML
            safe_message = escape(message)

            # Create TwiML response
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{safe_message}</Say>
    <Pause length="2"/>
    <Say voice="alice">
        This is an automated alert.
        Please check the monitoring dashboard.
    </Say>
</Response>"""

            call = self.twilio_client.calls.create(
                to=normalized_phone,
                from_=settings.twilio_phone_number,
                twiml=twiml
            )

            logger.info(
                f"Voice call initiated to {phone_number}: SID={call.sid}"
            )

            return {
                "status": "ringing",
                "call_sid": call.sid,
                "phone_number": phone_number,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                f"Failed to initiate voice call to {normalized_phone}: {e}"
            )

            return {
                "status": "failed",
                "error": str(e),
                "phone_number": normalized_phone
            }

    async def text_to_speech(
        self,
        text: str,
        language: str = "en"
    ) -> Optional[bytes]:
        """Convert text to speech audio."""
        global gTTS

        if not settings.enable_tts:
            logger.warning("TTS is disabled")
            return None

        if gTTS is None:
            try:
                from gtts import gTTS as gtts_class
                gTTS = gtts_class
            except ImportError:
                gTTS = False
        if not gTTS:
            logger.warning(
                "gTTS is not installed. TTS unavailable."
            )
            return None

        try:
            tts = gTTS(
                text=text,
                lang=language,
                slow=False
            )

            # gTTS requires a file-like object
            audio_buffer = BytesIO()

            tts.write_to_fp(audio_buffer)

            # Move back to beginning of buffer
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.read()

            logger.info("TTS conversion completed")

            return audio_bytes

        except Exception as e:
            logger.error(
                f"TTS conversion failed: {e}"
            )

            return None

    async def generate_emergency_message(
        self,
        incident_data: dict
    ) -> str:
        """Generate a formatted emergency message."""

        incident_type = incident_data.get(
            "incident_type",
            "Unknown incident"
        )

        location = incident_data.get(
            "location_name",
            "Unknown location"
        )

        severity = incident_data.get(
            "severity",
            "Unknown"
        )

        timestamp = incident_data.get(
            "created_at",
            "Unknown time"
        )

        message = (
            "Alert. This is an AI-generated emergency notification. "
            f"A {severity.lower()} incident has been detected. "
            f"Incident type: {incident_type}. "
            f"Location: {location}. "
            f"Time: {timestamp}. "
            "Please check the emergency dashboard immediately."
        )

        return message

    async def generate_police_notification(
        self,
        incident_data: dict
    ) -> str:
        """Generate a police notification message."""

        incident_type = incident_data.get(
            "incident_type",
            "Unknown"
        )

        location = incident_data.get(
            "location_name",
            "Unknown"
        )

        camera_id = incident_data.get(
            "camera_id",
            "Unknown"
        )

        message = (
            "Police alert. High priority incident detected. "
            f"Type: {incident_type}. "
            f"Location: {location}. "
            f"Camera ID: {camera_id}. "
            "Please respond immediately."
        )

        return message

    async def generate_ambulance_notification(
        self,
        incident_data: dict,
        hospital_data: dict
    ) -> str:
        """Generate an ambulance/hospital notification message."""

        location = incident_data.get(
            "location_name",
            "Unknown"
        )

        hospital_name = hospital_data.get(
            "hospital_name",
            "Nearest hospital"
        )

        distance = hospital_data.get(
            "estimated_distance_km",
            "Unknown"
        )

        message = (
            "Emergency medical response required. "
            f"Incident location: {location}. "
            f"Dispatch to: {hospital_name}. "
            f"Distance: approximately {distance} kilometers. "
            "Please proceed immediately."
        )

        return message


class MockNotificationService:
    """Mock notification service for demo/testing."""

    def health(self) -> dict:
        return {
            "sms_provider": "demo",
            "configured": True,
            "sender_configured": True,
            "credentials_present": False,
            "configuration_error": None,
            "simulated": True,
        }

    async def send_sms(
        self,
        phone_number: str,
        message: str
    ) -> dict:
        """Mock SMS sending."""

        logger.info(
            f"[DEMO] SMS to {phone_number}: {message}"
        )

        return {
            "status": "SMS_ACCEPTED",
            "provider": "demo",
            "simulated": True,
            "message_sid": (
                f"demo-sms-{datetime.utcnow().timestamp()}"
            ),
            "phone_number": phone_number,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def send_voice_alert(
        self,
        phone_number: str,
        message: str,
        message_type: str = "normal"
    ) -> dict:
        """Mock voice call."""

        logger.info(
            f"[DEMO] Voice call to {phone_number}: {message}"
        )

        return {
            "status": "ringing",
            "call_sid": (
                f"demo-call-{datetime.utcnow().timestamp()}"
            ),
            "phone_number": phone_number,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def stop_voice_call(self, call_sid: str) -> dict:
        logger.info("[DEMO] Voice call stopped: %s", call_sid)
        return {"status": "stopped", "call_sid": call_sid}

    async def text_to_speech(
        self,
        text: str,
        language: str = "en"
    ) -> Optional[bytes]:
        """Mock TTS."""

        logger.info(
            f"[DEMO] TTS: {text}"
        )

        return b"mock-audio-data"

    async def generate_emergency_message(
        self,
        incident_data: dict
    ) -> str:
        """Generate emergency message."""

        return await NotificationService().generate_emergency_message(
            incident_data
        )

    async def generate_police_notification(
        self,
        incident_data: dict
    ) -> str:
        """Generate police notification."""

        return await NotificationService().generate_police_notification(
            incident_data
        )

    async def generate_ambulance_notification(
        self,
        incident_data: dict,
        hospital_data: dict
    ) -> str:
        """Generate ambulance notification."""

        return await NotificationService().generate_ambulance_notification(
            incident_data,
            hospital_data
        )


def get_notification_service():
    """
    Get appropriate notification service based on configuration.

    Demo mode:
        Uses MockNotificationService.

    Production mode:
        Uses NotificationService.
    """

    if settings.demo_mode:
        return MockNotificationService()
    return NotificationService()