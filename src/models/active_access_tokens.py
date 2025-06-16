from datetime import datetime, timezone, timedelta

from sqlalchemy import Integer, Column, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship

from src.cores.config import settings
from src.cores.database import Base


class ActiveAccessToken(Base):
    __tablename__ = "active_access_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    access_token = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    user = relationship("User", back_populates="active_access_tokens")
