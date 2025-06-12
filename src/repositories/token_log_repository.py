from typing import Optional

from sqlalchemy import text
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
            action=log.action
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    def get_paginated(self, skip: int, limit: int) -> list[type[TokenLog]]:
        return self.db.query(TokenLog).offset(skip).limit(limit).all()

    def get_last_log(self, user_id: int, action: str) -> Optional[TokenLog]:
        sql = text("""SELECT * FROM token_logs
            WHERE user_id = :user_id And action = :action
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        result = self.db.execute(sql, {"user_id": user_id, "action": action}).fetchone()
        if result:
            # Nếu muốn trả về đối tượng TokenLog (ORM), bạn có thể map thủ công hoặc tạo đối tượng từ dict
            return TokenLog(**result._mapping)  # _mapping trả về dict như row
        return None


