from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BlacklistedTokenCreate(BaseModel):
    token: str


class BlacklistedTokenRead(BaseModel):
    id: int
    token: str
    blacklisted_at: datetime
    model_config = ConfigDict(from_attributes=True)
