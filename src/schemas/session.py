from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    user_id: str
    refresh_token: str
    ip_address: str
    user_agent: str
    expires_at: datetime


class SessionRead(BaseModel):
    id: int
    user_id: str
    refresh_token: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    revoked: bool

    model_config = ConfigDict(from_attributes=True)
