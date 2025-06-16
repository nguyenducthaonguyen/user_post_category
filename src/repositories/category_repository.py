from sqlalchemy.orm import Session

from src.models.categories import Category
from src.schemas.categories import CategoryCreate


class CategoryRepository:
    def __init__(self, db: Session):
        """
        Khởi tạo repository với một phiên làm việc DB (Session).
        """
        self.db = db

    def create(self, category: CategoryCreate):
        category = Category(**category.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get(self, category_id: str) -> Category | None:
        category = self.db.get(Category, category_id)
        if category is None:
            return None
        return category

    def update(self, category: Category):
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category_id: str):
        category = self.get(category_id)
        if category is None:
            return None
        self.db.delete(category)
        self.db.commit()
        return category

    def get_all(self) -> list[type[Category]]:
        return self.db.query(Category).all()

    def get_by_name(self, name: str):
        return self.db.query(Category).filter(Category.name == name).first()
