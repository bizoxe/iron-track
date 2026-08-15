from datetime import datetime
from enum import StrEnum
from re import compile as re_compile
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    EmailStr,
    Field,
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


NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]


class RoleSlug(StrEnum):
    """Available user role slugs."""

    SUPERUSER = "superuser"
    FITNESS_TRAINER = "fitness-trainer"


class PasswordValidator(
    RegexValidator,
    # Printable ASCII minus space ([!-~]): the space is rejected on purpose —
    # a pasted or typed invisible character must fail validation, not become
    # part of the stored hash.
    pattern=re_compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])[!-~]{8,128}$"),
    error_message="The password must be 8 to 128 characters long and include at least one uppercase letter, "
    "one lowercase letter, one number and one special character",
):
    """Validator for user passwords."""


class User(CamelizedBaseStruct, omit_defaults=True):
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
    deleted_at: datetime | None = None


class UserAuth(CamelizedBaseStruct, dict=True):
    """User model used for authentication context."""

    id: UUID
    name: str | None
    email: str
    is_active: bool
    is_superuser: bool
    role_slug: str

    def __post_init__(self) -> None:
        self._refresh_jti: str | None = None
        self._refresh_exp: float | None = None


class UserCreate(CamelizedBaseSchema):
    """Properties required to create a new user."""

    name: str | None = None
    email: NormalizedEmail
    password: Annotated[str, PasswordValidator]
    is_active: bool = True


class UserUpdate(UserCreate):
    """Schema for optional user account updates."""

    email: Annotated[NormalizedEmail, Field(default=None)]
    password: Annotated[str, PasswordValidator, Field(default=None)]
    is_active: Annotated[bool, Field(default=None)]


class AccountRegister(CamelizedBaseSchema):
    """Information provided by a user during public registration."""

    name: str | None = None
    email: NormalizedEmail
    password: Annotated[str, PasswordValidator]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.confirm_password != self.password:
            msg = "Passwords don't match"
            raise ValueError(msg)
        return self


class PasswordUpdate(CamelizedBaseSchema):
    """Input data for password rotation."""

    current_password: str
    new_password: Annotated[str, PasswordValidator]


class UserRoleAdd(CamelizedBaseSchema):
    """Payload for assigning a specific role to a user."""

    role_slug: RoleSlug


class UserRoleRevoke(UserRoleAdd):
    """Payload for revoking a specific role from a user."""
