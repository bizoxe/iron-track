from __future__ import annotations

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from typing import (
    TYPE_CHECKING,
    Any,
)
from uuid import uuid4

from joserfc import jwt

from app.config.base import get_settings

if TYPE_CHECKING:
    from joserfc.jwk import OKPKey
    from joserfc.jwt import Token

settings = get_settings()


def encode_jwt(
    payload: dict[str, Any],
    key_obj: OKPKey = settings.jwt.key_object,
    algorithm: str = settings.jwt.ALGORITHM,
    expire_minutes: int = settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    """Encode a JWT based on the provided payload and expiration settings.

    This function adds standard claims: `iat` (issued at), `exp` (expiration),
    and `jti` (JWT ID) to the token payload before encoding.

    Args:
        payload (dict): The base data to include in the token (e.g., user ID, email).
        key_obj (OKPKey): The private key used for signing the token.
            Defaults to the application's configured private key.
        algorithm (str): The cryptographic algorithm used for signing (e.g., 'Ed25519').
            Defaults to the configured algorithm.
        expire_minutes (int): The token's lifespan in minutes, used only if
            `expire_timedelta` is not provided.
        expire_timedelta (timedelta | None): Explicit timedelta defining the token's total lifespan.
            Overrides `expire_minutes`. Used primarily for Refresh Tokens.

    Returns:
        str: The encoded JWT string.
    """
    to_encode = payload.copy()
    time_now = datetime.now(tz=UTC)
    expire = time_now + expire_timedelta if expire_timedelta else time_now + timedelta(minutes=expire_minutes)

    to_encode.update(
        iat=time_now,
        exp=expire,
        jti=str(uuid4()),
    )
    return jwt.encode(
        header={"alg": algorithm},
        claims=to_encode,
        key=key_obj,
        algorithms=[algorithm],
    )


def decode_jwt(
    token: str | bytes,
    key_obj: OKPKey = settings.jwt.key_object,
    algorithm: str = settings.jwt.ALGORITHM,
) -> Token:
    """Decode and validate a JWT using the application's key.

    This function automatically verifies the token's signature and standard claims
    (such as expiration time).

    Args:
        token (str | bytes): The encoded JWT string or bytes to be decoded.
        key_obj (OKPKey): The key used for verifying the token's signature.
            Defaults to the application's configured key.
        algorithm (str): The cryptographic algorithm used for verification (e.g., 'Ed25519').
            Defaults to the configured algorithm.

    Returns:
        Token: The extracted token object, which contains header and claims.

    Raises:
        joserfc.errors.BadSignatureError: If the token signature verification fails.
        joserfc.errors.InvalidPayloadError: If the token's payload is not a valid JSON object.
    """
    return jwt.decode(
        value=token,
        key=key_obj,
        algorithms=[algorithm],
    )
