from typing import Optional

from sqlalchemy.orm import Session

from src.models.token_logs import TokenLog
from src.schemas.token_log import TokenLogCreate


class TokenLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: TokenLogCreate) -> TokenLog:
        db_log = TokenLog(
            user_id=log.user_id,
            username=log.username,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            action=log.action,
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    def get_paginated(self, skip: int, limit: int) -> list[type[TokenLog]]:
        return self.db.query(TokenLog).offset(skip).limit(limit).all()

    def get_last_log(self, user_id: str, action: str) -> Optional[TokenLog]:
        """
        Trả về log mới nhất cho user và action chỉ định.
        Args:
            user_id (str): ID của user.
            action (str): Loại action (ví dụ: 'login', 'refresh').
        Returns:
            TokenLog | None: Log mới nhất hoặc None nếu không có.
        """
        return self.db.query(TokenLog).filter(TokenLog.user_id == user_id, TokenLog.action == action).order_by(TokenLog.timestamp.desc()).first()
