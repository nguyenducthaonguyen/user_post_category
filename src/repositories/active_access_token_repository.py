from datetime import datetime, timezone
from os import access

from sqlalchemy.orm import Session

from src.models.active_access_tokens import ActiveAccessToken
from src.schemas.active_access_tokens import ActiveAccessTokenCreate


class ActiveAccessTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, token_data: ActiveAccessTokenCreate) -> ActiveAccessToken:
        db_token = ActiveAccessToken(**token_data.model_dump())
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_access_tokens_by_user_id(
        self, user_id: str
    ) -> list[type[ActiveAccessToken]]:
        access_tokens = (
            self.db.query(ActiveAccessToken).filter_by(user_id=user_id).all()
        )
        return access_tokens

    def delete_token(self, token: str):
        deleted_count = (
            self.db.query(ActiveAccessToken)
            .filter_by(access_token=token)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted_count > 0

    def delete_tokens_by_user_id(self, user_id: str) -> bool:
        try:
            deleted_count = (
                self.db.query(ActiveAccessToken)
                .filter_by(user_id=user_id)
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return deleted_count > 0
        except Exception as e:
            self.db.rollback()
            print("Failed to delete token by user id", e)
            return False

    def delete_expired_tokens(self):
        expired_tokens = (
            self.db.query(ActiveAccessToken)
            .filter(ActiveAccessToken.expires_at < datetime.now(timezone.utc))
            .all()
        )
        for token in expired_tokens:
            self.db.delete(token)
        self.db.commit()
        return len(expired_tokens)
