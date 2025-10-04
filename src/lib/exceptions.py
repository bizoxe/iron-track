from uuid import UUID


class Base(Exception):  # noqa: N818
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.headers = headers


class UnauthorizedException(Base):
    def __init__(
        self,
        message: str = "Not authenticated",
    ) -> None:
        super().__init__(
            status_code=401,
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFound(Base):
    def __init__(
        self,
        user_id: UUID | int | str,
    ) -> None:
        super().__init__(
            status_code=404,
            message=f"User {user_id!r} was not found",
        )


class BadRequestException(Base):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=400,
            message=message,
        )


class ConflictException(Base):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=409,
            message=message,
        )


class PermissionDeniedException(Base):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=403,
            message=message,
        )
