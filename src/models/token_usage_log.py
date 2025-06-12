from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Index

from src.cores.database import Base


class TokenUsageLog(Base):
    __tablename__ = "token_usage_log"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_token_time", "token", "requested_at"),
    )