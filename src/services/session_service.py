from datetime import datetime

from sqlalchemy.orm import Session
from src.repositories.session_repository import SessionRepository
from src.schemas.session import SessionCreate
from src.models.sessions import Session as SessionModel

class SessionService:
    def __init__(self, db: Session):
        self.repo = SessionRepository(db)

    def create_session(self, session_data: SessionCreate) -> SessionModel:
        return self.repo.add_session(session_data)

    def get_session_by_token(self, refresh_token: str) -> SessionModel | None:
        return self.repo.get_by_refresh_token(refresh_token)

    def validate_refresh_session(self, refresh_token: str) -> bool:
        session = self.repo.get_by_refresh_token(refresh_token)
        if not session:
            return False
        if session.revoked:
            return False
        if session.expires_at < datetime.now(datetime.now().tzinfo):
            return False
        return True

    def revoke_session(self, refresh_token: str) -> bool:
        session = self.repo.get_by_refresh_token(refresh_token)

        if session:
            self.repo.revoke_session(session)
            return True
        return False


    def revoke_all_sessions(self, user_id: str):
        self.repo.revoke_all_sessions(user_id)

    def cleanup_expired_sessions(self):
        self.repo.delete_expired_sessions()