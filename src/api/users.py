from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.cores.dependencies import get_current_user, get_db
from src.models.users import User
from src.schemas.response import MessageResponse, PaginatedResponse, StandardResponse
from src.schemas.users import PasswordChangeRequest, UserRead, UserUpdateRequest
from src.services.user_service import UserService

router = APIRouter()


# ✅ Local dependency cho service, chỉ dùng trong file này
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/", response_model=PaginatedResponse[UserRead])
def list_active_users(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng/trang"),
    service: UserService = Depends(get_user_service),
):
    return service.get_all(page, limit, True)


@router.get("/me", response_model=StandardResponse[UserRead])
def get_current_user_info(
    request: Request, service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    user = service.get_user_by_id(current_user.id)
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "Current user info retrieved successfully",
            "data": [UserRead.model_validate(user).model_dump()],
        },
    )


@router.get("/{user_id}", response_model=StandardResponse[UserRead])
def get_user_by_id(user_id: str, service: UserService = Depends(get_user_service)):
    user = service.get_user_by_id(user_id)
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "User found",
            "data": [UserRead.model_validate(user).model_dump()],
        },
    )


@router.put("/me", response_model=StandardResponse[UserRead])
def update_current_user_info(
    request: Request,
    user_update: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
):
    current_user = request.state.user
    user = service.update_user(current_user.id, user_update)
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "User updated successfully",
        },
    )


@router.patch("/me/change-password", response_model=StandardResponse)
def change_current_user_password(
    request: Request,
    password_data: PasswordChangeRequest,
    service: UserService = Depends(get_user_service),
):
    current_user = request.state.user
    return service.update_user_password(current_user.id, password_data)


@router.delete("/me", response_model=StandardResponse)
def deactivate_current_user(
    request: Request, service: UserService = Depends(get_user_service)
):
    current_user = request.state.user
    service.block_user(current_user.id)
    return JSONResponse(
        status_code=200,
        content={"status_code": 200, "message": "User block successfully"},
    )
