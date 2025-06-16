from pydantic import BaseModel, ConfigDict
from datetime import datetime


class BlacklistedTokenCreate(BaseModel):
    token: str


class BlacklistedTokenRead(BaseModel):
    id: int
    token: str
    blacklisted_at: datetime
    model_config = ConfigDict(from_attributes=True)
