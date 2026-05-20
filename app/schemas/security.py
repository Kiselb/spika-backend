from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TelegramLoginRequest(BaseModel):
    telegram_id: int
    telegram: Optional[str] = None   # может отсутствовать или быть null
    bot_secret: str
