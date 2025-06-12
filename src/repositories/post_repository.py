from typing import Optional

from sqlalchemy.orm import Session

from src.models import User
from src.models.posts import Post


class PostRepository:
    def __init__(self, db: Session):
        """
        Khởi tạo repository với một phiên làm việc DB (Session).
        """
        self.db = db


    def get(self, post_id: str) -> Optional[Post]:
        """
        Lấy bài post theo post_id.
        Trả về Post hoặc None nếu không tìm thấy.
        """
        return self.db.query(Post).filter(Post.id == post_id).first()

    def create(self, post: Post) -> Post:
        """
        Tạo mới bài post trong DB.
        """
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_posts_by_user_id(self, user_id: str) -> list[type[Post]]:
        """
        Lấy danh sách tất cả bài post của user có user_id.
        """
        return self.db.query(Post).filter(Post.user_id == user_id).all()

    def get_all(self, skip: int, limit: int, is_active: Optional[bool]):
        query = self.db.query(Post)
        if is_active is not None:
            query = query.join(User).filter(User.is_active == is_active)
        return query.offset(skip).limit(limit).all()

    def count_posts(self, is_active: Optional[bool] = None) -> int:
        query = self.db.query(Post)
        if is_active is not None:
            query = query.join(User).filter(User.is_active == is_active)
        return query.count()


    def update(self, post: Post) -> Post:
        """
        Commit và refresh post đã được cập nhật thuộc tính bên ngoài.
        """
        self.db.commit()
        self.db.refresh(post)
        return post


    def delete(self, post: Post):
        """
        Xóa bài post khỏi DB.
        """
        self.db.delete(post)
        self.db.commit()
