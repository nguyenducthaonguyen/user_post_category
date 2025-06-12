from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.active_access_tokens import ActiveAccessToken
from src.repositories.active_access_token_repository import ActiveAccessTokenRepository
from src.schemas.active_access_tokens import ActiveAccessTokenCreate
from src.schemas.response import MessageResponse


class ActiveAccessTokenService:
    def __init__(self, db: Session):
        self.repo = ActiveAccessTokenRepository(db)

    def create_token(self, token_create: ActiveAccessTokenCreate) -> ActiveAccessToken:
        return self.repo.add(token_create)

    def get_tokens_by_user_id(self, user_id: str) -> List[ActiveAccessToken]:
        return self.repo.get_access_tokens_by_user_id(user_id)

    def delete_token(self, token: str) -> MessageResponse:
        try:
            deleted = self.repo.delete_token(token)
            if deleted:
                return MessageResponse(detail="Token deleted successfully")
            else:
                raise HTTPException(status_code=404, detail="Token not found")
        except Exception:
            raise HTTPException(status_code=400, detail="Deletion failed")

    def delete_tokens_by_user_id(self, user_id: str) -> MessageResponse:
        try:
            deleted = self.repo.delete_tokens_by_user_id(user_id)
            if deleted:
                return MessageResponse(detail="Tokens deleted successfully")
            else:
                raise HTTPException(status_code=404, detail="No tokens found for user")
        except Exception:
            raise HTTPException(status_code=400, detail="Deletion failed")

    def cleanup_expired_tokens(self):
        self.repo.delete_expired_tokens()