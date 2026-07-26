from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_password_reset_url(token: str) -> str:
    query = urlencode({"token": token})
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?{query}"


def send_password_reset_email(recipient_email: str, recipient_name: str, token: str) -> None:
    """Deliver a password-reset message through the configured SMTP server.

    The raw token is used only to construct the outbound link. It is never stored in the database.
    Delivery errors are logged without exposing the token or changing the public API response.
    """

    reset_url = build_password_reset_url(token)
    safe_name = escape(recipient_name)
    safe_url = escape(reset_url, quote=True)
    minutes = settings.PASSWORD_RESET_EXPIRE_MINUTES

    message = EmailMessage()
    message["Subject"] = "Reset your ATLAS password"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(
        "\n".join(
            [
                f"Hello {recipient_name},",
                "",
                "A password reset was requested for your ATLAS account.",
                f"Open this link within {minutes} minutes:",
                reset_url,
                "",
                "If you did not request this change, you can ignore this email.",
                "The link can be used only once.",
            ]
        )
    )
    message.add_alternative(
        f"""
        <html>
          <body style="font-family:Arial,sans-serif;color:#0f172a;line-height:1.6">
            <h2>Reset your ATLAS password</h2>
            <p>Hello {safe_name},</p>
            <p>A password reset was requested for your ATLAS account.</p>
            <p>
              <a href="{safe_url}" style="display:inline-block;padding:12px 18px;background:#4f46e5;color:#fff;text-decoration:none;border-radius:8px;font-weight:700">
                Reset password
              </a>
            </p>
            <p>This link expires in {minutes} minutes and can be used only once.</p>
            <p>If you did not request this change, you can safely ignore this email.</p>
          </body>
        </html>
        """,
        subtype="html",
    )

    try:
        if settings.SMTP_USE_SSL:
            smtp_connection: smtplib.SMTP = smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
                context=ssl.create_default_context(),
            )
        else:
            smtp_connection = smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )

        with smtp_connection as smtp:
            smtp.ehlo()
            if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception:
        logger.exception("Password-reset email delivery failed for %s", recipient_email)
