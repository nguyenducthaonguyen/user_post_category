from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String
from sqlalchemy.orm import relationship

from src.cores.database import Base
from src.models.base import BaseMixin
from src.models.enums import GenderEnum, RoleEnum


class User(BaseMixin, Base):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    fullname = Column(String(100))
    role = Column(SqlEnum(RoleEnum), default=RoleEnum.user)
    is_active = Column(Boolean, default=True)
    gender = Column(SqlEnum(GenderEnum), nullable=False)

    posts = relationship("Post", back_populates="user")
    active_access_tokens = relationship("ActiveAccessToken", back_populates="user")
    sessions = relationship("Session", back_populates="user")
