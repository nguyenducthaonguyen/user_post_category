from datetime import datetime

from sqlalchemy.orm import Session

from src.models.token_usage_log import TokenUsageLog
from src.models.blacklisted_tokens import BlacklistedToken
from src.models.active_access_tokens import ActiveAccessToken


class RateLimiterRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_token_usage(self, token: str, since: datetime) -> int:
        return (
            self.db.query(TokenUsageLog)
            .filter(TokenUsageLog.token == token)
            .filter(TokenUsageLog.requested_at >= since)
            .count()
        )

    def log_token_usage(self, token: str, timestamp: datetime):
        self.db.add(TokenUsageLog(token=token, requested_at=timestamp))
        self.db.commit()

    def blacklist_token(self, token: str):
        self.db.query(ActiveAccessToken).filter(
            ActiveAccessToken.access_token == token
        ).delete()

        # Check nếu đã tồn tại rồi thì khỏi insert
        exists = (
            self.db.query(BlacklistedToken)
            .filter(BlacklistedToken.token == token)
            .first()
        )

        if not exists:
            self.db.add(BlacklistedToken(token=token))
            self.db.commit()

    def delete_expired_tokens(self, expire_before: datetime):
        expired_tokens = (
            self.db.query(TokenUsageLog)
            .filter(TokenUsageLog.requested_at < expire_before)
            .all()
        )
        print(f"[DEBUG] Tokens to delete: {len(expired_tokens)}")

        for token in expired_tokens:
            self.db.delete(token)
        self.db.commit()
        return len(expired_tokens)
