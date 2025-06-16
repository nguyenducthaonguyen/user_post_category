from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.cores.dependencies import get_db
from src.models.enums import RoleEnum
from src.schemas.response import PaginatedResponse, StandardResponse
from src.schemas.token_log import TokenLogResponse
from src.schemas.users import UserReadAdmin
from src.services.token_log_service import TokenLogService
from src.services.user_service import UserService

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_token_log_service(db: Session = Depends(get_db)) -> TokenLogService:
    return TokenLogService(db)


@router.get("", response_model=PaginatedResponse[UserReadAdmin])
def list_users(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng/trang"),
    name: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(
        None, description="Trạng thái người dùng: true = active, false = blocked"
    ),
    role: Optional[RoleEnum] = Query(None, description="Vai trò của người dùng"),
    service: UserService = Depends(get_user_service),
):
    """
    Lấy danh sách người dùng theo trạng thái.
    """
    return service.get_all_for_admin(page, limit, name, is_active, role)


@router.get("/users/{user_id}", response_model=StandardResponse)
def get_user(user_id: str, service: UserService = Depends(get_user_service)):
    """
    Lấy thông tin chi tiết người dùng theo ID.
    """
    data_user = service.get_user_by_id_for_admin(user_id)
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "Get user successfully",
            "data": [UserReadAdmin.model_validate(data_user).model_dump()],
        },
    )


@router.patch("/users/{user_id}/block", response_model=StandardResponse)
def block_user(user_id: str, service: UserService = Depends(get_user_service)):
    """
    Admin khóa tài khoản người dùng.
    """
    service.block_user_for_admin(user_id)
    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "block success"}
    )


@router.patch("/users/{user_id}/unblock", response_model=StandardResponse)
def unblock_user(user_id: str, service: UserService = Depends(get_user_service)):
    """
    Admin mở khóa tài khoản người dùng.
    """
    service.unblock_user_for_admin(user_id)
    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "unblock success"}
    )


@router.delete("/users/{user_id}", response_model=StandardResponse)
def delete_user(user_id: str, service: UserService = Depends(get_user_service)):
    """
    Admin xóa người dùng cùng tất cả bài viết của họ.
    """
    service.delete_user(user_id)
    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "Deleted Successfully"}
    )


@router.get("/token", response_model=StandardResponse)
def get_token_logs(token_service: TokenLogService = Depends(get_token_log_service)):
    tokens = token_service.get_paginated()
    return ORJSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "success",
            "data": [
                TokenLogResponse.model_validate(token).model_dump() for token in tokens
            ],
        },
    )
