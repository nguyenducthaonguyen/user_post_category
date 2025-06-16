from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models.sessions import Session as SessionModel
from src.schemas.session import SessionCreate


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_refresh_token(self, refresh_token: str):
        return self.db.query(SessionModel).filter_by(refresh_token=refresh_token).first()

    def add_session(self, session_data: SessionCreate) -> SessionModel:
        db_session = SessionModel(**session_data.model_dump())  # ✅ Chuyển Pydantic -> SQLAlchemy
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def revoke_session(self, session: SessionModel):
        session.revoked = True
        self.db.commit()

    def revoke_all_sessions(self, user_id: str):
        sessions = self.db.query(SessionModel).filter_by(user_id=user_id, revoked=False).all()
        for s in sessions:
            s.revoked = True
        self.db.commit()

    def delete_expired_sessions(self):
        now = datetime.now(timezone.utc)
        expired_sessions = self.db.query(SessionModel).filter(SessionModel.expires_at < now).all()
        for s in expired_sessions:
            self.db.delete(s)
        self.db.commit()
