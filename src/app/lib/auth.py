from typing import Any

from fastapi import (
    Request,
)
from fastapi.openapi.models import (
    APIKey,
    APIKeyIn,
)
from fastapi.security.base import SecurityBase

from app.config.base import get_settings
from app.lib.exceptions import UnauthorizedException

__all__ = (
    "access_token",
    "refresh_token",
)


settings = get_settings()


class JWTCookieSecurity(SecurityBase):
    """FastAPI security scheme for identifying a JWT authentication token.

    Defines how the token should be extracted from the request (via the __call__ method)
    and provides metadata for OpenAPI documentation.
    """

    def __init__(
        self,
        authentication_token: str,
        scheme_name: str | None = None,
        *,
        auto_error: bool = True,
    ) -> None:
        self.scheme_name = scheme_name or self.__class__.__name__
        self._authentication_token = authentication_token
        self.auto_error = auto_error
        api_key_kwargs: dict[str, Any] = {
            "type": "apiKey",
            "in": APIKeyIn.cookie,
            "name": self._authentication_token,
            "description": "An authentication token (JWT) is stored in the HTTP-only Cookie"
            f" '{self._authentication_token}'.",
        }
        self.model = APIKey(
            **api_key_kwargs,
        )

    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get(self._authentication_token)
        if token is not None:
            return token

        if self.auto_error:
            raise UnauthorizedException
        return None


access_token = JWTCookieSecurity(authentication_token="access_token")
refresh_token = JWTCookieSecurity(authentication_token="refresh_token")
