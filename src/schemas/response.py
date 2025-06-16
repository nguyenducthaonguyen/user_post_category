from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, HttpUrl, constr

from src.schemas.users import UserReadAdmin


class PaginationSchema(BaseModel):
    total: int
    limit: int
    offset: int


class LinkSchema(BaseModel):
    self: HttpUrl
    next: Optional[HttpUrl] = None
    last: HttpUrl


class MessageResponse(BaseModel):
    detail: str


T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T]


class ErrorResponse(BaseModel):
    status_code: int
    error: str
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: List[T]
    pagination: PaginationSchema
    link: LinkSchema


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    id: str
    username: str
    role: str
