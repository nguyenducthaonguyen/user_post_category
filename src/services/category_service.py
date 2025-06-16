from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.cores.exceptions import APIException
from src.repositories.category_repository import CategoryRepository
from src.schemas.categories import CategoryCreate, CategoryUpdate, CategoryRead


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def get_category_by_id(self, category_id: str):
        category = self.repo.get(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    def get_all_categories(self):
        try:
            categories = self.repo.get_all()
            return categories
        except Exception as e:
            # Custom trả về lỗi có field "content"
            raise HTTPException(
                status_code=400, detail=f"Failed to retrieve categories: {str(e)}"
            )

    def create_category(self, category_in: CategoryCreate) -> CategoryRead:
        try:
            # Kiểm tra tên trùng nếu cần
            if self.repo.get_by_name(category_in.name):
                raise HTTPException(
                    status_code=400, detail="Category name already exists"
                )
            # Tạo mới
            new_category = self.repo.create(category_in)
            return new_category
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create category: {str(e)}"
            )

    def update_category(self, category_id: str, category_in: CategoryUpdate):
        category = self.repo.get(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        # Check tên trùng nếu cần
        existing = self.repo.get_by_name(category_in.name)
        if existing and existing.id != category_id:
            raise APIException(
                error="loi", status_code=400, detail="Category name already exists"
            )
        # Cập nhật
        for field, value in category_in.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        try:
            category_data = self.repo.update(category)
            # category_data = CategoryRead.model_validate(category).model_dump() nếu muốn chuyển qua json
            return category_data
        except Exception as e:
            self.repo.db.rollback()
            raise HTTPException(
                status_code=400, detail=f"Failed to update category: {str(e)}"
            )

    def delete_category(self, category_id: str):
        category = self.repo.get(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        try:
            self.repo.delete(category_id)
            return category
        except Exception as e:
            self.repo.db.rollback()
            raise HTTPException(
                status_code=400, detail=f"Failed to delete category: {str(e)}"
            )
