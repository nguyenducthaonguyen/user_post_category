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

    def get_tokens_by_user_id(self, user_id: str):
        return self.repo.get_access_tokens_by_user_id(user_id)

    from fastapi import HTTPException

    def delete_token(self, token: str):
        try:
            deleted = self.repo.delete_token(token)
            if deleted:
                return deleted
            else:
                raise HTTPException(status_code=404, detail="Token not found")
        except HTTPException:
            # Để HTTPException tự ném ra, không bắt lại
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Deletion failed: {str(e)}")

    def delete_tokens_by_user_id(self, user_id: str):
        try:
            deleted = self.repo.delete_tokens_by_user_id(user_id)
            if deleted:
                return deleted
            else:
                raise HTTPException(status_code=404, detail="No tokens found for user")
        except HTTPException:
            # Để HTTPException tự ném ra, không bắt lại
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Deletion failed")

    def cleanup_expired_tokens(self):
        return self.repo.delete_expired_tokens()
