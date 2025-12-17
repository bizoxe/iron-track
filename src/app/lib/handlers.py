from fastapi import (
    Request,
    Response,
)
from fastapi.exceptions import RequestValidationError

from app.lib.exceptions import BaseAPIException
from app.lib.json_response import MsgSpecJSONResponse


async def http_exception_handler(
    request: Request,
    exc: BaseAPIException,
) -> Response:
    """Handle application exceptions by returning a structured JSON response.

    Args:
        request (Request): The request object.
        exc (BaseAPIException): The custom application exception instance.

    Returns:
        Response: A JSON response containing the error message and status code.
    """
    return MsgSpecJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Handle validation errors by structuring error details.

    Args:
        request (Request): The request object.
        exc (RequestValidationError): The validation exception.

    Returns:
        Response: A JSON response (422 status code) containing structured error details.
    """
    errors = [{"type": err["type"], "field": err["loc"][0], "message": err["msg"]} for err in exc.errors()]

    return MsgSpecJSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": errors},
    )
