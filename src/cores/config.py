import os
from enum import Enum
from typing import Optional
from pydantic import MySQLDsn
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    DATABASE_URL: MySQLDsn
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    BLACKLIST_TOKEN_EXPIRE_MINUTES: int = 30
    TOKEN_USAGE_LOG_EXPIRE_MINUTES: int = 1
    RATE_LIMIT_MAX_REQUESTS: int = 10
    RATE_LIMIT_PERIOD_SECONDS: int = 10
    SUSPICIOUS_LOGIN_TIME_WINDOW: int = 300  # 5 minutes in seconds
    SUSPICIOUS_REFRESH_TIME_WINDOW: int = 86400  # 24 hours in seconds

    SITE_DOMAIN: str = "myapp.com"
    ENVIRONMENT: Environment = Environment.PRODUCTION
    SENTRY_DSN: Optional[str] = None

    CORS_ORIGINS: list[str]
    CORS_ORIGINS_REGEX: Optional[str] = None
    CORS_HEADERS: list[str]

    APP_VERSION: str = "1.0"

    @classmethod
    def from_env(cls) -> "Settings":
        if "DATABASE_URL" not in os.environ:
            raise RuntimeError("Missing required environment variable: DATABASE_URL")
        if "SECRET_KEY" not in os.environ:
            raise RuntimeError("Missing required environment variable: SECRET_KEY")

        return cls(
            DATABASE_URL=os.environ["DATABASE_URL"],
            SECRET_KEY=os.environ["SECRET_KEY"],
        )

    model_config = {
        "env_file": ".env.test",
    }


# ✅ Khởi tạo settings từ environment
settings = Settings.from_env()
