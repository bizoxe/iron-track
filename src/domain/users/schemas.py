from datetime import (
    date,
    datetime,
)
from enum import StrEnum
from re import compile as re_compile
from typing import (
    Annotated,
    Self,
)
from uuid import UUID

from annotated_types import (
    MaxLen,
    MinLen,
)
from pydantic import (
    BaseModel,
    EmailStr,
    PrivateAttr,
    model_validator,
)

from src.lib.pretty_regex_error_msgs import regex_validator

__all__ = (
    "AccountRegister",
    "PasswordUpdate",
    "User",
    "UserAuth",
    "UserCreate",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserUpdate",
)

valid_pwd = regex_validator(
    pattern=re_compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"),
    error_message="The password must contain a minimum of eight characters, at least one uppercase letter, one "
    "lowercase letter, one number and one special character",
)


class User(BaseModel):
    """User properties to use for a response."""

    id: UUID
    name: str | None = None
    email: str
    is_active: bool = False
    is_superuser: bool = False
    role_name: str
    role_slug: str
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: Annotated[str, MinLen(3), MaxLen(20)]
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: Annotated[str, MinLen(3), MaxLen(20)] | None = None
    is_active: bool | None = True
    is_superuser: bool | None = False


class AccountRegister(BaseModel):
    name: str | None = None
    email: EmailStr
    password: Annotated[str, valid_pwd]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.confirm_password != self.password:
            msg = "Passwords don't match"
            raise ValueError(msg)
        return self


class UserAuth(User):
    joined_at: date
    _refresh_jti: str | None = PrivateAttr(default=None)


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: Annotated[str, valid_pwd]


class RoleSlug(StrEnum):
    SUPERUSER = "superuser"
    FITNESS_TRAINER = "fitness-trainer"


class UserRoleAdd(BaseModel):
    """User role add ."""

    role_slug: RoleSlug


class UserRoleRevoke(UserRoleAdd):
    """User role revoke ."""
