
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
except Exception:
    pass


class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL must be set to a MySQL SQLAlchemy URI (e.g. mysql+pymysql://user:pass@host/db)"
        )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret")

    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    MAIL_SENDER = os.environ.get("MAIL_SENDER", "no-reply@example.com")
