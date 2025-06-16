from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from src.models import Session as SessionModels
from src.models.posts import Post
from src.models.users import RoleEnum, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _commit_and_refresh(self, obj: User):
        try:
            self.db.commit()
            self.db.refresh(obj)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get(self, user_id: str):
        user = self.db.get(User, user_id)
        return user

    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_users_by_role_user(self) -> list[type[User]]:
        return self.db.query(User).filter(User.role == RoleEnum.user).all()

    def update_user(self, user: User):
        self._commit_and_refresh(user)

    def update_password(self, user: User, new_password_hash: str):
        user.password = new_password_hash
        self._commit_and_refresh(user)

    def block_user(self, user: User):
        user.is_active = False
        self._commit_and_refresh(user)

    def unblock_user(self, user: User):
        user.is_active = True
        self._commit_and_refresh(user)

    def list_users(
        self, status: Optional[bool] = None, skip: int = 0, limit: int = 100
    ) -> list[type[User]]:
        query = self.db.query(User)
        if status is not None:
            query = query.filter(User.is_active == status)
        return query.offset(skip).limit(limit).all()

    def delete_user_and_posts(self, user: User):
        try:
            self.db.query(Post).filter(Post.user_id == user.id).delete(
                synchronize_session=False
            )
            self.db.query(SessionModels).filter(
                SessionModels.user_id == user.id
            ).delete(synchronize_session=False)

            self.db.delete(user)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    @staticmethod
    def _filter_by_name_and_status(
        query,
        name: Optional[str],
        is_active: Optional[bool],
        role: Optional[RoleEnum],
    ):
        if name:
            query = query.filter(User.fullname.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if role is not None:
            query = query.filter(User.role == role)
        return query

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        role: Optional[RoleEnum] = None,
    ) -> List[User]:
        query = self.db.query(User).options(joinedload(User.posts))
        query = self._filter_by_name_and_status(query, name, is_active, role)
        return query.offset(skip).limit(limit).all()

    def count_users(
        self,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        role: Optional[RoleEnum] = None,
    ) -> int:
        query = self.db.query(func.count(User.id))
        query = self._filter_by_name_and_status(query, name, is_active, role)
        return query.scalar()
