from fastapi import Request
from fastapi.exceptions import RequestValidationError

from src.lib.exceptions import Base
from src.lib.json_response import MsgSpecJSONResponse


async def http_exception_handler(
    request: Request,
    exc: Base,
) -> MsgSpecJSONResponse:
    return MsgSpecJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> MsgSpecJSONResponse:
    errors = [{"type": err["type"], "field": err["loc"][0], "message": err["msg"]} for err in exc.errors()]

    return MsgSpecJSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": errors},
    )
