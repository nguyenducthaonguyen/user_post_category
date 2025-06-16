from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from src.cores.database import Base
from src.models.base import BaseMixin
from src.models.post_category import post_category


class Category(BaseMixin, Base):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, nullable=False)
    posts = relationship("Post", secondary=post_category, back_populates="categories")
