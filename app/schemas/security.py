from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class RoleSimple(BaseModel):
    role_id: int
    role_name: str
    model_config = {"from_attributes": True}

class TelegramLoginRequest(BaseModel):
    telegram_id: int
    telegram: Optional[str] = None   # может отсутствовать или быть null
    bot_secret: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    roles: List[RoleSimple]
