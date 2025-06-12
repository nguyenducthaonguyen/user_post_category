import uuid

from pydantic import BaseModel


class BaseRequest(BaseModel):
    id: uuid.UUID
    name: str

class UsersResponse(BaseModel):
    name: str
    age: int

class BaseResponse(BaseModel):
    status_code: int
    message: str
    data: UsersResponse

class BaseRepository:

    def __init__(self, session, model):
        self.session = session
        self.model = model


    def list(self, user: BaseRequest):
        query = self.session.query(self.model)
        if user.id is not None:
            query = query.filter(self.model.id == user.id)

        if user.name is not None:
            query = query.filter(self.model.name == user.name)

        result = query.all()
        return result

    def get(self, user: BaseRequest):
        pass

    def create(self, user: BaseRequest):
        pass

    def update(self, user: BaseRequest):
        pass

    def delete(self, user: BaseRequest):
        pass


from ..models.users import User

class UsersRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, User)