import datetime
from typing import Any

import jwt

from config.base import get_settings

settings = get_settings()


def encode_jwt(
    payload: dict[str, Any],
    private_key: str = settings.jwt.OAUTH_JWT_PRIVATE_KEY.read_text(),
    algorithm: str = settings.jwt.ALGORITHM,
    expire_minutes: int = settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: datetime.timedelta | None = None,
) -> str:
    to_encode = payload.copy()
    time_now = datetime.datetime.now(datetime.timezone.utc)
    if expire_timedelta:
        expire = time_now + expire_timedelta
    else:
        expire = time_now + datetime.timedelta(minutes=expire_minutes)

    to_encode.update(
        iat=time_now,
        exp=expire,
    )
    return jwt.encode(
        payload=to_encode,
        key=private_key,
        algorithm=algorithm,
    )


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.jwt.OAUTH_JWT_PUBLIC_KEY.read_text(),
    algorithm: str = settings.jwt.ALGORITHM,
) -> dict[str, Any]:
    to_decode: dict[str, Any] = jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=[algorithm],
    )
    return to_decode
