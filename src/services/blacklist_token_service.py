from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.schemas.blacklist_token import BlacklistedTokenCreate
from src.repositories.blacklist_token_repository import BlacklistedTokenRepository


class BlacklistTokenService:
    def __init__(self, db: Session):
        self.repo = BlacklistedTokenRepository(db)

    def blacklist_token(self, token: str):
        token_data = BlacklistedTokenCreate(token=token)
        return self.repo.add(token_data)

    def is_token_blacklisted(self, token: str) -> bool:
        return self.repo.is_blacklisted(token)

    def cleanup_expired_tokens(self, expire_minutes):
        expire_time = datetime.now(timezone.utc) - timedelta(minutes=expire_minutes)
        # Xóa tất cả token blacklist có blacklisted_at < expire_time
        return self.repo.delete_expired_tokens(expire_time)

