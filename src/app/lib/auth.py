from typing import Any

from fastapi import Request
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase

from app.lib.exceptions import UnauthorizedException


class JWTCookieSecurity(SecurityBase):
    """FastAPI security scheme for identifying a JWT authentication token.

    This scheme extracts the JWT from an HTTP-only cookie. It implements
    the `__call__` protocol to function as a FastAPI dependency and provides
    necessary metadata for OpenAPI documentation.
    """

    def __init__(
        self,
        authentication_token: str,
        scheme_name: str | None = None,
        *,
        auto_error: bool = True,
    ) -> None:
        self.authentication_token = authentication_token
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error
        api_key_kwargs: dict[str, Any] = {
            "type": "apiKey",
            "in": APIKeyIn.cookie,
            "name": self.authentication_token,
            "description": f"JWT authentication token from the HTTP-only cookie '{self.authentication_token}'.",
        }
        self.model = APIKey(
            **api_key_kwargs,
        )

    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get(self.authentication_token)
        if token is not None:
            return token

        if self.auto_error:
            raise UnauthorizedException
        return None


access_token = JWTCookieSecurity(authentication_token="access_token")
refresh_token = JWTCookieSecurity(authentication_token="refresh_token")
