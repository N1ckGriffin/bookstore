
import os
from pathlib import Path

try:
    from dotenv import dotenv_values

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        env = dotenv_values(dotenv_path=env_path)
    else:
        env = {}
except Exception:
    env = {}


class Config:
    DATABASE_URL = env.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL must be set to a MySQL SQLAlchemy URI (e.g. mysql+pymysql://user:pass@host/db)"
        )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = env.get("JWT_SECRET_KEY", "dev-secret")

    SMTP_HOST = env.get("SMTP_HOST")
    SMTP_PORT = int(env.get("SMTP_PORT", "465"))
    SMTP_USER = env.get("SMTP_USER")
    SMTP_PASSWORD = env.get("SMTP_PASSWORD")
    MAIL_SENDER = env.get("MAIL_SENDER", "no-reply@example.com")
