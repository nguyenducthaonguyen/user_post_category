from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.models import Category
from src.repositories import UserRepository, CategoryRepository
from src.repositories.post_repository import PostRepository
from src.schemas.posts import PostCreate, PostUpdate, PostRead
from src.models.posts import Post
from src.models.users import User


class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.post_repo = PostRepository(db)
        self.user_repo = UserRepository(db)
        self.category_repo = CategoryRepository(db)

    def _get_user_and_check_status(self, user_id: str) -> User:
        """
        Lấy user theo user_id và kiểm tra trạng thái hoạt động.
        Nếu không tìm thấy hoặc user bị block, raise HTTPException.
        """
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is blocked")
        return user


    def _model_dum_response_data(self, posts):
        return [PostRead.model_validate(post).model_dump() for post in posts]


    def create_post(self, post_data: PostCreate, user_id: str):
        try:
            categories = []
            if post_data.category_ids:
                categories = self.db.query(Category).filter(Category.id.in_(post_data.category_ids)).all()
            new_post = Post(
            title=post_data.title,
            content=post_data.content,
            user_id=user_id,
            )
            new_post.categories = categories
            data_post = self.post_repo.create(new_post)
            return data_post
        except Exception as e:
            raise HTTPException (status_code=400, detail=f"Create post failed: {e}")


    def get_posts_by_user_id(self, user_id: str):
        """
        Lấy tất cả bài post của user theo user_id.
        Kiểm tra trạng thái user trước khi truy vấn.
        """
        self._get_user_and_check_status(user_id)
        try:
            posts = self.post_repo.get_posts_by_user_id(user_id)
            return posts
        except Exception as e:
           raise HTTPException(status_code=400, detail=f"Get posts by user failed: {e}")


    def get_post_by_id(self, post_id: str) -> Post:
        """
        Lấy bài post theo post_id.
        Kiểm tra trạng thái user sở hữu bài post.
        Nếu không tìm thấy post hoặc user không hợp lệ, raise HTTPException.
        """
        post = self.post_repo.get(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        self._get_user_and_check_status(post.user_id)
        return post


    def get_all(
            self,
            page: Optional[int] = 0,
            limit: Optional[int] = 100,
            is_active: Optional[bool] = None

    ) :
        """
        Lấy tất cả bài post. Nếu is_active != None thì lọc theo trạng thái user.
        Có hỗ trợ phân trang.
        """
        try:
            skip = (page - 1) * limit
            total = self.post_repo.count_posts(is_active)
            posts = self.post_repo.get_all(skip,limit,is_active)
            last_page = (total - 1) // limit + 1
            return JSONResponse(
                status_code=200,
                content={
                    "status_code": 200,
                    "message":"Get Posts Successfully",
                    "data": self._model_dum_response_data(posts),
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": skip
                    },
                    "link": {
                        "self": f"http://127.0.0.1:8000/api/v1/posts?page={page}&limit={limit}&is_active={is_active}",
                        "next": f"http://127.0.0.1:8000/api/v1/posts?page={page + 1}&limit={limit}&is_active={is_active}" if page < last_page else None,
                        "last": f"http://127.0.0.1:8000/api/v1/posts?page={last_page}&limit={limit}&is_active={is_active}"
                    }
                }
            )

        except Exception as e:
            raise HTTPException( status_code=400, detail=f"Get posts failed: {e}")

    def _get_post_and_check_owner(self, post_id: str, user_id: str):
        post = self.post_repo.get(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post Not Found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="User Not The Post Owner")
        return post

    def update_post(self, post_id: str, post_update: PostUpdate, user_id: str):
        post = self._get_post_and_check_owner(post_id, user_id)
        try:
        # Cập nhật thuộc tính ở đây
            categories = []
            if post_update.category_ids:
                categories = self.db.query(Category).filter(Category.id.in_(post_update.category_ids)).all()
            post.title = post_update.title
            post.content = post_update.content
            post.categories = categories

            post = self.post_repo.update(post)
            return post
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Update post failed: {e}")

    def delete_post(self, post_id: str, user_id: str):
        try:
            post = self._get_post_and_check_owner(post_id, user_id)
            self.post_repo.delete(post)
            return post
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Delete post failed: {e}")