from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.cores.database import Base
from src.models.base import BaseMixin
from src.models.post_category import post_category


class Post(BaseMixin, Base):
    __tablename__ = "posts"

    title = Column(String(100), nullable=False)
    content = Column(Text)
    user_id = Column(String(36), ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")

    categories = relationship(
        "Category", secondary=post_category, back_populates="posts"
    )
