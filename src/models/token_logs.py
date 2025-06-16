from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from src.cores.database import Base


class TokenLog(Base):
    __tablename__ = "token_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String(36), index=True, nullable=True
    )  # có thể null nếu chưa xác thực user
    username = Column(String(255), nullable=True)
    ip_address = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False)  # ví dụ: "login", "refresh"
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
