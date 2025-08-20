from fastapi import Request

from library.exceptions import Base
from library.json_response import MsgSpecJSONResponse


async def custom_exception_handler(
    request: Request,
    exc: Base,
) -> MsgSpecJSONResponse:
    return MsgSpecJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )
