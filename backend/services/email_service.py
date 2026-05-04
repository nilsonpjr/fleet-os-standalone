import os
import smtplib
from email.message import EmailMessage

from core.logger import get_logger

logger = get_logger("email_service")


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() != "false"
PUBLIC_NOTIFICATIONS_TO_EMAIL = os.getenv("PUBLIC_NOTIFICATIONS_TO_EMAIL")


def send_public_notification_email(subject: str, body: str):
    recipient = PUBLIC_NOTIFICATIONS_TO_EMAIL or SMTP_FROM_EMAIL
    required = [SMTP_HOST, SMTP_PORT, SMTP_FROM_EMAIL, recipient]
    if not all(required):
        logger.warning("SMTP not configured for public notifications; email skipped.")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        logger.info(f"Public notification email sent to {recipient}")
    except Exception as exc:
        logger.error(f"Failed to send public notification email: {exc}")
