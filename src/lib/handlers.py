from fastapi import (
    Request,
    Response,
)
from fastapi.exceptions import RequestValidationError

from src.lib.exceptions import BaseAPIException
from src.lib.json_response import MsgSpecJSONResponse


async def http_exception_handler(
    request: Request,
    exc: BaseAPIException,
) -> Response:
    """Handle custom application exceptions by returning a structured JSON response."""
    return MsgSpecJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Handle Pydantic validation errors by structuring error details."""
    errors = [{"type": err["type"], "field": err["loc"][0], "message": err["msg"]} for err in exc.errors()]

    return MsgSpecJSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": errors},
    )
