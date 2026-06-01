from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.mod_account import ModRole


class ModLogin(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105  oauth token type, not a secret


class ModAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: ModRole
    is_active: bool
    created_at: datetime


class BanCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    board_id: int | None = None  # null bans the ip across all boards


class BanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_hash: str
    board_id: int | None
    reason: str | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
