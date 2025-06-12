from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.schemas.posts import PostCreate, PostUpdate, PostRead

from src.models.users import User
from src.cores.dependencies import get_current_user, get_db
from src.schemas.response import MessageResponse, StandardResponse, PaginatedResponse, ErrorResponse
from src.services.post_service import PostService


router = APIRouter()


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(db)


@router.get("/", response_model=PaginatedResponse[PostRead])
def get_all_posts(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng/trang"),
    service: PostService = Depends(get_post_service)
):
    return service.get_all(page, limit, True)


@router.get("/me", response_model=StandardResponse[list[PostRead]],
            responses={
                400: {"model": ErrorResponse, "description": "Bad request"},
            })
def get_my_posts(
        request: Request,
        service: PostService = Depends(get_post_service)):
    current_user = request.state.user
    return service.get_posts_by_user_id(current_user.id)


@router.get("/users/{user_id}", response_model=StandardResponse[list[PostRead]],
            responses={
                400: {"model": ErrorResponse, "description": "Bad request"},
                403: {"model": ErrorResponse, "description": "Forbidden"},
                404: {"model": ErrorResponse, "description": "Not found"}
            })
def get_posts_by_user(user_id: str, service: PostService = Depends(get_post_service)):
    return service.get_posts_by_user_id(user_id)


@router.post("/", response_model=StandardResponse[PostRead])
def create_post(
    request: Request,
    post: PostCreate,
    service: PostService = Depends(get_post_service)
):
    current_user = request.state.user
    return service.create_post(post, current_user.id)



@router.put("/{post_id}", response_model=StandardResponse)
def update_post(request: Request, post_id: str, post: PostUpdate, service: PostService = Depends(get_post_service)):
    current_user = request.state.user
    return service.update_post(post_id, post, current_user.id)


@router.get("/{post_id}", response_model=StandardResponse)
def get_post(post_id: str, service: PostService = Depends(get_post_service)):
    post=service.get_post_by_id(post_id)
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "get post successfully",
            "data": [PostRead.model_validate(post).model_dump()]
        }
    )


@router.delete("/{post_id}", response_model=StandardResponse)
def delete_post(request: Request, post_id: str,  service: PostService = Depends(get_post_service)):
    current_user = request.state.user
    return service.delete_post(post_id, current_user.id)
