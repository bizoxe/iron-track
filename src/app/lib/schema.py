from collections.abc import Sequence
from typing import Annotated, Any

from advanced_alchemy.utils.text import camelize
from msgspec import Struct
from pydantic import BaseModel as BaseSchema
from pydantic import ConfigDict, Field


class BaseStruct(Struct):
    """Base msgspec structure for API responses."""


class CamelizedBaseStruct(BaseStruct, rename="camel"):
    """Camelized base msgspec structure for frontend responses."""


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=camelize,
        extra="forbid",
        use_enum_values=True,
        from_attributes=False,
        frozen=True,
    )


class BasePage[T](BaseStruct):
    """Base envelope for paginated list results."""

    items: Sequence[T]
    total: int
    limit: int
    offset: int


class ErrorInfo(BaseSchema):
    """Generic application error structure."""

    message: Annotated[
        str,
        Field(description="Error description message.", examples=["An error occurred while processing the request"]),
    ]
    details: Annotated[
        dict[str, Any] | None,
        Field(
            description="Additional error context.",
            examples=[{"reason": "invalid_state"}],
        ),
    ] = None


class ValidationErrorDetail(BaseSchema):
    """Detailed information about a specific validation error."""

    type: Annotated[str, Field(description="Error type")]
    field: Annotated[str, Field(description="Field name")]
    message: Annotated[str, Field(description="Error message")]


class ValidationErrorSchema(BaseSchema):
    """Schema for input data validation errors."""

    message: Annotated[str, Field(json_schema_extra={"example": "Validation Error"})]
    details: Annotated[
        list[ValidationErrorDetail],
        Field(
            json_schema_extra={
                "example": [
                    {
                        "type": "string_too_short",
                        "field": "password",
                        "message": "String should have at least 3 characters",
                    }
                ]
            }
        ),
    ]
