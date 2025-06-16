from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.cores.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(255))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime, default=datetime.now(timezone.utc))
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")
