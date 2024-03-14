from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    login: str
    password: str
    role: str
    allowed: bool
