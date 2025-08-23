from __future__ import annotations

from re import Pattern
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
    def get_pydantic_core_schema(
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        schema = chain_schema(
            steps=[
                handler(source),
                custom_error_schema(
                    schema=str_schema(pattern=pattern),
                    custom_error_type="value_error",
                    custom_error_context={"error": error_message},
                ),
            ]
        )
        return schema

    return GetPydanticSchema(get_pydantic_core_schema)
