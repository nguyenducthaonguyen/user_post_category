from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.cores import auth
from src.models.enums import RoleEnum
from src.repositories.user_repository import UserRepository
from src.schemas.users import UserUpdateRequest, PasswordChangeRequest, UserRead, UserReadAdmin

from src.models.users import User

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_user_by_id(self, user_id: str):
        user = self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User blocked")
        return user

    def get_user_by_email(self, email: str) -> User:
        user = self.repo.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


    def update_user(self, user_id: str, update_data: UserUpdateRequest):
        user = self.get_user_by_id(user_id)

        if update_data.email != user.email:
            existing_user = self.repo.get_user_by_email(str(update_data.email))
            if existing_user and existing_user.id != user_id:
                raise HTTPException(status_code=400, detail="Email already registered")

        user.email = update_data.email
        user.fullname = update_data.fullname
        user.gender = update_data.gender

        self.repo.update_user(user)
        return user

    def update_user_password(self, user_id: str, data: PasswordChangeRequest):
        user = self.get_user_by_id(user_id)

        if not auth.verify_password(data.password_old, user.password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        if data.password != data.password_confirmation:
            raise HTTPException(status_code=422, detail="Password confirmation does not match")

        new_password_hash = auth.get_password_hash(data.password)
        self.repo.update_password(user, new_password_hash)

        return JSONResponse(
            status_code=200,
            content={
                "status_code":200,
                "message":"Change password successfully"
            }
        )

    def block_user(self, user_id: str):
        user = self.get_user_by_id(user_id)
        self.repo.block_user(user)
        return user

    def get_all(self, page: int, limit: int, is_active: Optional[bool]) :
        try:
            skip = (page - 1) * limit
            total = self.repo.count_users(is_active=is_active)
            users = self.repo.get_all(skip=skip, limit=limit, is_active=is_active)
            last_page = (total - 1) // limit + 1
            return JSONResponse(
                status_code=200,
                content={
                    "status_code": 200,
                    "message": "Get Users Successfully",
                    "data": [UserRead.model_validate(user).model_dump() for user in users],
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": skip
                    },
                    "link": {
                        "self": f"http://127.0.0.1:8000/api/v1/users?page={page}&limit={limit}&is_active={is_active}",
                        "next": f"http://127.0.0.1:8000/api/v1/users?page={page + 1}&limit={limit}&is_active={is_active}" if page < last_page else None,
                        "last": f"http://127.0.0.1:8000/api/v1/users?page={last_page}&limit={limit}&is_active={is_active}"
                    }
                }
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while retrieving users: {str(e)}")

    # Admin-specific services
    def get_user_by_id_for_admin(self, user_id: str) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def block_user_for_admin(self, user_id: str):
        user = self.get_user_by_id_for_admin(user_id)
        print(user.is_active)
        if not user.is_active:
            raise HTTPException(status_code=400, detail="User was already blocked")
        self.repo.block_user(user)
        print(user.is_active)
        return user

    def unblock_user_for_admin(self, user_id: str):
        user = self.get_user_by_id_for_admin(user_id)
        if user.is_active:
            raise HTTPException(status_code=400, detail="User was already unblocked")
        self.repo.unblock_user(user)
        return user


    def delete_user(self, user_id: str):
        user = self.get_user_by_id_for_admin(user_id)

        try:
            self.repo.delete_user_and_posts(user)
            return user

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while deleting the user: {str(e)}")

    def get_all_for_admin(self, page: int, limit: int, name: Optional[str] = None, is_active: Optional[bool] = None, role: Optional[RoleEnum] = None):
        skip = (page - 1) * limit
        users = self.repo.get_all(skip=skip, limit=limit, name=name, is_active=is_active, role=role)
        total = self.repo.count_users(name=name, is_active=is_active, role=role)

        last_page = (total - 1) // limit + 1

        return {
            "status_code": 200,
            "message": "Success",
            "data": [UserReadAdmin.model_validate(user).model_dump() for user in users],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": skip
            },
            "link": {
                "self": f"http://127.0.0.1:8000/api/v1/admin?page={page}&limit={limit}&name={name}&is_active={is_active}",
                "next": f"http://127.0.0.1:8000/api/v1/admin?page={page + 1}&limit={limit}&name={name}&is_active={is_active}" if page < last_page else None,
                "last": f"http://127.0.0.1:8000/api/v1/admin?page={last_page}&limit={limit}&name={name}&is_active={is_active}"
            }
        }