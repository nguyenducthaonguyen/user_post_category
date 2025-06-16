from typing import Optional, List

from pydantic import BaseModel, constr, ConfigDict

from src.schemas.categories import CategoryRead


# Schema cơ bản cho bài viết
class PostBase(BaseModel):
    title: constr(min_length=3, max_length=255)  # Tiêu đề bài viết
    content: Optional[str] = None
    categories: Optional[List[CategoryRead]] = None


# Schema dùng để tạo bài viết
class PostCreate(BaseModel):
    title: constr(min_length=3, max_length=255)  # Tiêu đề bài viết
    content: Optional[str] = None
    category_ids: Optional[List[str]] = None


# Schema dùng để cập nhật bài viết
class PostUpdate(PostCreate):
    pass


# Schema dùng để đọc dữ liệu bài viết trả về client
class PostRead(BaseModel):
    id: str
    title: constr(min_length=3, max_length=255)  # Tiêu đề bài viết
    content: Optional[str] = None
    categories: Optional[List[CategoryRead]] = None
    user_id: str

    model_config = ConfigDict(from_attributes=True)
