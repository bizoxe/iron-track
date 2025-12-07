from datetime import (
    UTC,
    datetime,
    timedelta,
)
from typing import Any
from uuid import uuid4

import jwt

from app.config.base import get_settings

settings = get_settings()


def encode_jwt(
    payload: dict[str, Any],
    private_key: str = settings.jwt.auth_jwt_private_key,
    algorithm: str = settings.jwt.ALGORITHM,
    expire_minutes: int = settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    """Encode a JWT based on the provided payload and expiration settings.

    This function adds standard claims: 'iat' (issued at), 'exp' (expiration),
    and 'jti' (JWT ID) to the token payload before encoding.

    Args:
        payload (dict): The base data to include in the token (e.g., user ID, email).
        private_key (str): The private key used for signing the token. Defaults
            to the application's configured private key.
        algorithm (str): The cryptographic algorithm used for signing (e.g., 'RS256').
            Defaults to the configured algorithm.
        expire_minutes (int): The token's lifespan in minutes, used only if
            `expire_timedelta` is not provided.
        expire_timedelta (timedelta | None): Explicit timedelta defining the token's total lifespan.
            Overrides `expire_minutes`. Used primarily for Refresh Tokens.

    Returns:
        The encoded JWT string.
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
        payload=to_encode,
        key=private_key,
        algorithm=algorithm,
    )


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.jwt.auth_jwt_public_key,
    algorithm: str = settings.jwt.ALGORITHM,
) -> dict[str, Any]:
    """Decode and validate a JWT using the application's public key.

    This function automatically verifies the token's signature and standard claims
    (such as expiration time).

    Args:
        token (str | bytes): The encoded JWT string or bytes to be decoded.
        public_key (str): The public key used for verifying the token's signature.
            Defaults to the application's configured public key.
        algorithm (str): The cryptographic algorithm used for verification (e.g., ['RS256']).
            Defaults to the configured algorithm.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        jwt.InvalidSignatureError: If the token signature is invalid.
        jwt.ExpiredSignatureError: If the token's expiration time has passed.
        jwt.DecodeError: If the token cannot be decoded for other reasons.
    """
    to_decode: dict[str, Any] = jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=[algorithm],
    )
    return to_decode
