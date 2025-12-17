from __future__ import annotations

from re import Pattern  # noqa: TC003
from typing import (
    TYPE_CHECKING,
    Any,
)

from pydantic import (
    GetPydanticSchema,
    validate_call,
)
from pydantic_core.core_schema import (
    chain_schema,
    custom_error_schema,
    str_schema,
)

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core.core_schema import CoreSchema


@validate_call
def regex_validator(pattern: Pattern[str], error_message: str) -> GetPydanticSchema:
    """Create a Pydantic validator that checks a string against a regex pattern.

    If validation fails, a custom "value_error" with the provided message is raised,
    improving error readability compared to default Pydantic errors.

    Args:
        pattern (Pattern[str]): The compiled regular expression pattern to enforce.
        error_message (str): The custom error message to display on validation failure.

    Returns:
        GetPydanticSchema: A Pydantic object to be used in model field annotations.
    """

    def get_pydantic_core_schema(
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return chain_schema(
            steps=[
                handler(source),
                custom_error_schema(
                    schema=str_schema(pattern=pattern),
                    custom_error_type="value_error",
                    custom_error_context={"error": error_message},
                ),
            ]
        )

    return GetPydanticSchema(get_pydantic_core_schema)
