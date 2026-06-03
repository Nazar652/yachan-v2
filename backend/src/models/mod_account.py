from enum import StrEnum
from typing import ClassVar

from sqlmodel import Field

from src.models.timestamps import TimestampMixin


class ModRole(StrEnum):
    ADMIN = "admin"
    MODERATOR = "moderator"


class ModAccount(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "mod_account"

    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    password_hash: str = Field(max_length=255)
    role: ModRole = Field(default=ModRole.MODERATOR)
    is_active: bool = Field(default=True)
