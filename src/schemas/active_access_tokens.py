from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActiveAccessTokenCreate(BaseModel):
    user_id : str
    access_token: str
    expires_at: datetime

class ActiveAccessTokenRead(ActiveAccessTokenCreate):
    id: int
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


 