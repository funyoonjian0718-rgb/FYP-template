import os
import smtplib
from email.message import EmailMessage

from app.core.settings import settings


def send_password_reset_email(to_email: str, token: str) -> None:
    smtp_host = settings.smtp_host or ""
    smtp_port = settings.smtp_port or 587
    smtp_user = settings.smtp_user or ""
    smtp_password = settings.smtp_password or ""
    from_email = settings.smtp_from_email or smtp_user or "noreply@example.com"

    if not smtp_host:
        raise RuntimeError("SMTP_HOST is not configured")

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(
        f"Use this reset token to reset your password:\n\n{token}\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(message)
