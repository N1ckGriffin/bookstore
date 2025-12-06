import smtplib
from email.message import EmailMessage
from typing import Dict

from backend.config import Config


def send_order_email(to_address: str, subject: str, body: str):
    """Send an email using SMTP configured via environment variables."""
    if not Config.SMTP_HOST or not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_SENDER
    msg["To"] = to_address
    msg.set_content(body)

    try:
        if Config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT) as smtp:
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                smtp.send_message(msg)
    except Exception:
        pass
