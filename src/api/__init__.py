from fastapi import APIRouter, Depends
from src.api import admin, posts, users, auth, categories
from src.cores.dependencies import require_roles
from src.models.users import RoleEnum

api_router = APIRouter()

api_router.include_router(
    posts.router,
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(require_roles(RoleEnum.admin, RoleEnum.user))],
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_roles(RoleEnum.admin, RoleEnum.user))],
)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(RoleEnum.admin))],
)

api_router.include_router(
    categories.router,
    prefix="/admin",
    tags=["categories"],
    dependencies=[Depends(require_roles(RoleEnum.admin))],
)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
