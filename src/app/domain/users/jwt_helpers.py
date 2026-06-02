from base64 import urlsafe_b64decode
from datetime import timedelta
from time import time
from typing import TYPE_CHECKING

from cashews import cache
from joserfc.errors import (
    JoseError,
)
from msgspec import (
    DecodeError,
    Struct,
    json,
    msgpack,
)
from structlog import get_logger

from app.config.base import get_settings
from app.lib.exceptions import UnauthorizedException
from app.lib.jwt_utils import decode_jwt, encode_jwt

if TYPE_CHECKING:
    from uuid import UUID


settings = get_settings()

log = get_logger()


class TokenPayloadBase(Struct):
    """Represents the base set of validated JWT claims."""

    iat: float
    exp: float
    jti: str
    sub: str

    @property
    def is_expired(self) -> bool:
        return self.exp <= time()


class TokenPayloadAccess(TokenPayloadBase):
    """Stores payload data specific to the access token."""

    email: str


class TokenPayloadRefresh(TokenPayloadBase):
    """Stores payload data specific to the refresh token."""


_encoder = msgpack.Encoder()
_access_decoder = msgpack.Decoder(TokenPayloadAccess)
_refresh_decoder = msgpack.Decoder(TokenPayloadRefresh)
_json_decoder = json.Decoder(TokenPayloadBase)


def get_unverified_jti(token: str) -> str | None:
    """Extract the jti claim from a JWT token without validation."""
    try:
        payload_segment = token.split(".")[1]
        payload_segment += "=" * (4 - len(payload_segment) % 4)
        payload_bytes = urlsafe_b64decode(payload_segment.encode("utf-8"))
        struct_obj = _json_decoder.decode(payload_bytes)
    except (IndexError, ValueError, DecodeError):
        return None
    else:
        return struct_obj.jti


def create_access_token(
    user_id: "UUID",
    email: str,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id (UUID): The unique identifier of the user.
        email (str): The user's email address.

    Returns:
        str: The encoded access token string.
    """
    jwt_payload = {
        "sub": str(user_id),
        "email": email,
    }
    return encode_jwt(payload=jwt_payload)


def create_refresh_token(user_id: "UUID") -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id (UUID): The unique identifier of the user.

    Returns:
        str: The encoded refresh token string.
    """
    jwt_payload = {
        "sub": str(user_id),
    }
    return encode_jwt(
        payload=jwt_payload,
        expire_timedelta=timedelta(
            days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )


async def get_access_token_payload(token: str) -> TokenPayloadAccess:
    """Decode an access token and validate its claims via cache fast-path.

    Args:
        token: The raw encoded JWT string.

    Returns:
        TokenPayloadAccess: The validated and parsed access token data.

    Raises:
        UnauthorizedException: If the token has expired, its signature
            is invalid, or internal deserialization fails.
    """
    token_id = get_unverified_jti(token=token)
    if token_id:
        cache_key = f"jwt:access:{token_id}"
        cached_data = await cache.get(key=cache_key)
        if cached_data:
            payload = _access_decoder.decode(cached_data)
            if not payload.is_expired:
                return payload
    try:
        token_obj = decode_jwt(token=token)
        claims = token_obj.claims

        payload = TokenPayloadAccess(**claims)
        if payload.is_expired:
            raise UnauthorizedException(message="Token has expired")

        now = time()
        ttl = int(payload.exp - now)
        if ttl > 0:
            serialized = _encoder.encode(payload)
            cache_key = f"jwt:access:{token_id}"
            await cache.set(key=cache_key, value=serialized, expire=ttl)

    except (JoseError, DecodeError) as exc:
        log.warning(
            "Access token decode failed",
            error_type=type(exc).__name__,
            error_detail=str(exc),
        )
        raise UnauthorizedException(message="Invalid token") from exc
    else:
        return payload


def get_refresh_token_payload(token: str) -> TokenPayloadRefresh:
    """Decode a refresh token and validate its claims.

    Args:
        token: The raw encoded JWT string.

    Returns:
        TokenPayloadRefresh: The validated and parsed refresh token data.

    Raises:
        UnauthorizedException: If the token has expired, its signature
            is invalid, or internal deserialization fails.
    """
    try:
        token_obj = decode_jwt(token=token)
        claims = token_obj.claims

        payload = TokenPayloadRefresh(**claims)
        if payload.is_expired:
            raise UnauthorizedException(message="Token has expired")

    except (JoseError, DecodeError) as exc:
        log.warning(
            "Refresh token decode failed",
            error_type=type(exc).__name__,
            error_detail=str(exc),
        )
        msg = "Invalid token"
        raise UnauthorizedException(message=msg) from exc
    else:
        return payload


async def add_token_to_blacklist(refresh_token_identifier: str, ttl: int) -> None:
    """Add a refresh token identifier (JTI) to cache for revocation."""
    await cache.set(
        key=f"revoked:{refresh_token_identifier}",
        value="1",
        expire=ttl,
    )


async def is_token_in_blacklist(refresh_token_identifier: str) -> bool:
    """Check if a refresh token identifier (JTI) exists in the blacklist."""
    return await cache.exists(f"revoked:{refresh_token_identifier}")
