from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.users import UserCreate
from src.cores import auth


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register_user(self, user_data: UserCreate) -> User:
        # Check username
        if self.repo.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        if self.repo.get_user_by_email(str(user_data.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        user_data.password = auth.get_password_hash(user_data.password)

        created_user = self.repo.create_user(User(**user_data.model_dump()))
        return created_user
