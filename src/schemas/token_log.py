from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TokenLogCreate(BaseModel):
    user_id: Optional[str]
    username: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    action: str

class TokenLogResponse(TokenLogCreate):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
