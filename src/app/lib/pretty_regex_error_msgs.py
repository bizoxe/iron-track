from __future__ import annotations

from re import Pattern  # noqa: TC003
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
)

from pydantic import validate_call
from pydantic_core.core_schema import (
    chain_schema,
    custom_error_schema,
    str_schema,
)

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core.core_schema import CoreSchema


class RegexValidator:
    """Base class for creating reusable Pydantic regex validators."""

    __slots__ = ()
    pattern: ClassVar[Pattern[str]]
    error_message: ClassVar[str]

    @classmethod
    @validate_call
    def __init_subclass__(cls, pattern: Pattern[str], error_message: str) -> None:
        """Configure the validator subclass with a specific regex pattern.

        Args:
            pattern (Pattern[str]): The compiled regular expression to validate against.
            error_message (str): The custom message returned when validation fails.
        """
        cls.pattern = pattern
        cls.error_message = error_message

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> CoreSchema:
        """Generate the Pydantic Core Schema for the validator.

        Integrates the custom regex check into the standard validation chain.
        """
        return chain_schema(
            steps=[
                handler(source),
                custom_error_schema(
                    schema=str_schema(pattern=cls.pattern),
                    custom_error_type="value_error",
                    custom_error_context={"error": cls.error_message},
                ),
            ]
        )
