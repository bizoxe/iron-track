import datetime
from uuid import UUID

from config.base import get_settings
from library.jwt_utils import encode_jwt

settings = get_settings()


def create_access_token(
    user_id: UUID,
    email: str,
) -> str:
    jwt_payload = {
        "sub": str(user_id),
        "email": email,
    }
    return encode_jwt(payload=jwt_payload)


def create_refresh_token(user_id: UUID) -> str:
    jwt_payload = {
        "sub": str(user_id),
    }
    return encode_jwt(
        payload=jwt_payload,
        expire_timedelta=datetime.timedelta(
            days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )
