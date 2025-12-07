class BaseAPIException(Exception):  # noqa: N818
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.headers = headers


class UnauthorizedException(BaseAPIException):
    def __init__(
        self,
        message: str = "Not authenticated",
    ) -> None:
        super().__init__(
            status_code=401,
            message=message,
        )


class UserNotFound(BaseAPIException):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=404,
            message="User not found",
        )


class BadRequestException(BaseAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=400,
            message=message,
        )


class ConflictException(BaseAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=409,
            message=message,
        )


class PermissionDeniedException(BaseAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=403,
            message=message,
        )


class NotFoundException(BaseAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=404,
            message=message,
        )
