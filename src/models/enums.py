from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"
