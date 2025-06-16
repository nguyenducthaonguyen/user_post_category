from datetime import datetime

from sqlalchemy.orm import Session
from src.models.blacklisted_tokens import BlacklistedToken
from src.schemas.blacklist_token import BlacklistedTokenCreate


class BlacklistedTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, token_data: BlacklistedTokenCreate) -> BlacklistedToken:
        db_token = BlacklistedToken(**token_data.model_dump())
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def is_blacklisted(self, token: str) -> bool:
        # Lọc đúng: filter nhận ColumnElement[bool]
        return (
            self.db.query(BlacklistedToken)
            .filter(BlacklistedToken.token == token)
            .first()
            is not None
        )

    def delete_expired_tokens(self, expire_before: datetime):
        expired_tokens = (
            self.db.query(BlacklistedToken)
            .filter(BlacklistedToken.blacklisted_at < expire_before)
            .all()
        )
        for token in expired_tokens:
            self.db.delete(token)
        self.db.commit()
        return len(expired_tokens)