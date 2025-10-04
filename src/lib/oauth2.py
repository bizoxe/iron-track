from fastapi import (
    Depends,
    Request,
)
from fastapi.openapi.models import OAuthFlowPassword
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param

from src.config.base import get_settings
from src.lib.exceptions import UnauthorizedException

__all__ = (
    "access_token",
    "login_required",
    "refresh_token",
)


settings = get_settings()


class OAuth2PwdBearerCookieBase(OAuth2):
    def __init__(
        self,
        authentication_token: str,
        token_url: str = settings.jwt.TOKEN_URL,
        scheme_name: str | None = None,
        scopes: dict[str, str] | None = None,
        *,
        auto_error: bool = True,
    ) -> None:
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl=token_url, scopes=scopes))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)
        self._authentication_token = authentication_token

    async def __call__(self, request: Request) -> str | None:
        authorization: str | None = request.cookies.get(self._authentication_token)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise UnauthorizedException
            return None

        return param


access_token = OAuth2PwdBearerCookieBase(authentication_token="access_token")
refresh_token = OAuth2PwdBearerCookieBase(authentication_token="refresh_token")
login_required = Depends(access_token)
