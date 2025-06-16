from typing import List

from fastapi import APIRouter, Depends, status

from src.cores.dependencies import get_db
from src.models import Session
from src.schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate
from src.schemas.response import ErrorResponse, StandardResponse
from src.services.category_service import CategoryService  # adjust import as needed

router = APIRouter(prefix="/categories")


def get_category_service(db: Session = Depends(get_db)):
    return CategoryService(db)


@router.get("/", response_model=StandardResponse[List[CategoryRead]])
def get_categories(service: CategoryService = Depends(get_category_service)):
    categories = service.get_all_categories()
    return StandardResponse(
        status_code=status.HTTP_200_OK,
        message="Categories retrieved successfully",
        data=categories,
    )


@router.post("/", response_model=StandardResponse[CategoryRead])
def create_category(
    category: CategoryCreate, service: CategoryService = Depends(get_category_service)
):
    category = service.create_category(category)
    return StandardResponse(
        status_code=status.HTTP_201_CREATED,
        message="Category created successfully",
        data=category,
    )


@router.patch(
    "/{category_id}",
    response_model=StandardResponse[CategoryRead],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)
def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
):
    return StandardResponse(
        status_code=status.HTTP_200_OK,
        message="Category updated successfully",
        data=service.update_category(category_id, category_update),
    )


@router.delete(
    "/{category_id}",
    response_model=StandardResponse[CategoryRead],
    responses={404: {"model": ErrorResponse, "description": "Not found"}},
)
def delete_category(
    category_id: str, service: CategoryService = Depends(get_category_service)
):
    service.get_category_by_id(category_id)
    return StandardResponse(
        status_code=status.HTTP_200_OK,
        message="Category deleted successfully",
        data=service.delete_category(category_id),
    )


@router.get(
    "/{category_id}",
    response_model=StandardResponse[CategoryRead],
    responses={404: {"model": ErrorResponse, "description": "Not found"}},
)
def get_category(
    category_id: str, service: CategoryService = Depends(get_category_service)
):
    category = service.get_category_by_id(category_id)
    return StandardResponse(
        status_code=status.HTTP_200_OK,
        message="Category retrieved successfully",
        data=category,
    )
