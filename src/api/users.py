from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.schemas.response import MessageResponse, StandardResponse, PaginatedResponse
from src.services.user_service import UserService
from src.models.users import User
from src.schemas.users import (UserRead, UserUpdateRequest, PasswordChangeRequest)
from src.cores.dependencies import get_db, get_current_user


router = APIRouter()


# ✅ Local dependency cho service, chỉ dùng trong file này
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/", response_model=PaginatedResponse[UserRead])
def list_active_users(
        page: int = Query(1, ge=1, description="Trang hiện tại"),
        limit: int = Query(10, ge=1, le=100, description="Số lượng/trang"),
        service: UserService = Depends(get_user_service)
):
    return service.get_all(page, limit, True)


@router.get("/me", response_model=StandardResponse[UserRead])
def get_current_user_info(
    request: Request,
    service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    return service.get_user_by_id(current_user.id)


@router.get("/{user_id}", response_model=StandardResponse[UserRead])
def get_user_by_id(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    return service.get_user_by_id(user_id)


@router.put("/me", response_model=StandardResponse[UserRead])
def update_current_user_info(
    request: Request,
    user_update: UserUpdateRequest,
    service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    return service.update_user(current_user.id, user_update)


@router.patch("/me/change-password", response_model=StandardResponse)
def change_current_user_password(
    request: Request,
    password_data: PasswordChangeRequest,
    service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    return service.update_user_password(current_user.id, password_data)


@router.delete("/me", response_model=StandardResponse)
def deactivate_current_user(
    request: Request,
    service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    return service.block_user(current_user.id)
