from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

