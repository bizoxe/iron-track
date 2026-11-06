from typing import Any


class BaseAPIException(Exception):  # noqa: N818
    """Base exception for all API-related errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        self.headers = headers


class BadRequestException(BaseAPIException):
    """400 Bad Request exception."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=400,
            message=message,
            details=details,
        )


class UnauthorizedException(BaseAPIException):
    """401 Unauthorized exception."""

    def __init__(
        self,
        message: str = "Not authenticated",
    ) -> None:
        super().__init__(
            status_code=401,
            message=message,
        )


class PermissionDeniedException(BaseAPIException):
    """403 Permission Denied exception."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=403,
            message=message,
            details=details,
        )


class NotFoundException(BaseAPIException):
    """404 Not Found exception."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=404,
            message=message,
            details=details,
        )


class UserNotFound(BaseAPIException):
    """404 User not found exception."""

    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=404,
            message="User not found",
        )


class ConflictException(BaseAPIException):
    """409 Conflict exception."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=409,
            message=message,
            details=details,
        )


class JWTKeyConfigError(RuntimeError):
    """Raised when the JWT private key is missing, corrupted, or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
