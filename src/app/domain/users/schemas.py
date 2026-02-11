from datetime import datetime
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
    EmailStr,
    model_validator,
)

from app.lib.pretty_regex_error_msgs import RegexValidator
from app.lib.schema import (
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

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


class PasswordValidator(
    RegexValidator,
    pattern=re_compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_])[A-Za-z\d@$!%*?&_]{8,}$"),
    error_message="The password must contain a minimum of eight characters, at least one uppercase letter, one "
    "lowercase letter, one number and one special character",
):
    """Validator for user passwords."""


class User(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    name: str | None
    email: str
    is_active: bool
    is_superuser: bool
    role_name: str
    role_slug: str
    created_at: datetime
    updated_at: datetime


class UserCreate(CamelizedBaseSchema):
    """Properties required to create a new user."""

    name: str | None = None
    email: EmailStr
    password: Annotated[str, MinLen(3), MaxLen(20)]
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(CamelizedBaseSchema):
    """Data transfer object for optional user account updates."""

    name: str | None = None
    email: EmailStr | None = None
    password: Annotated[str, MinLen(3), MaxLen(20)] | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class AccountRegister(CamelizedBaseSchema):
    """Information provided by a user during public registration."""

    name: str | None = None
    email: EmailStr
    password: Annotated[str, PasswordValidator]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        """Ensure the 'password' and 'confirm_password' fields match."""
        if self.confirm_password != self.password:
            msg = "Passwords don't match"
            raise ValueError(msg)
        return self


class UserAuth(CamelizedBaseStruct, dict=True):
    """User model used for authentication context."""

    id: UUID
    name: str | None
    email: str
    is_active: bool
    is_superuser: bool
    role_slug: str

    def __post_init__(self) -> None:
        self._refresh_jti = None


class PasswordUpdate(CamelizedBaseSchema):
    """Input data for password rotation."""

    current_password: str
    new_password: Annotated[str, PasswordValidator]


class RoleSlug(StrEnum):
    """Available user role slugs."""

    SUPERUSER = "superuser"
    FITNESS_TRAINER = "fitness-trainer"


class UserRoleAdd(CamelizedBaseSchema):
    """Payload for granting a specific role to a user."""

    role_slug: RoleSlug


class UserRoleRevoke(UserRoleAdd):
    """Payload for revoking a specific role from a user."""
