from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, Integer, String

from src.cores.database import Base


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=False, nullable=False)
    blacklisted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
