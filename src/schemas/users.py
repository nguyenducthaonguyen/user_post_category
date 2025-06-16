from pydantic import BaseModel, ConfigDict, EmailStr, constr, field_validator

from src.models.users import GenderEnum, RoleEnum


class UserCreate(BaseModel):
    """
    Schema dùng để nhận dữ liệu tạo mới User từ client
    """

    username: constr(min_length=3, max_length=100)
    password: constr(min_length=8, max_length=32)
    email: EmailStr
    fullname: constr(min_length=3, max_length=100)
    gender: GenderEnum


class UserRead(BaseModel):
    """
    Schema dùng để trả dữ liệu User cơ bản (không bao gồm mật khẩu) cho client
    """

    id: str
    username: constr(min_length=3, max_length=100)
    email: EmailStr
    fullname: constr(min_length=3, max_length=100)
    gender: GenderEnum
    role: RoleEnum

    model_config = ConfigDict(from_attributes=True)


class UserReadAdmin(UserRead):
    """
    Schema trả dữ liệu User dành cho admin,
    bao gồm thêm trường status để biết trạng thái tài khoản
    """

    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """
    Schema dùng để nhận dữ liệu cập nhật thông tin User
    """

    email: EmailStr
    fullname: constr(min_length=3, max_length=100)
    gender: GenderEnum


class PasswordChangeRequest(BaseModel):
    """
    Schema dùng để nhận dữ liệu đổi mật khẩu,
    bao gồm mật khẩu cũ, mật khẩu mới và xác nhận mật khẩu mới
    """

    password_old: constr(min_length=8, max_length=32)
    password: constr(min_length=8, max_length=32)
    password_confirmation: constr(min_length=8, max_length=32)
