from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeVar,
    cast,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exercises.schemas import ExerciseScope

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.exercises.utils import ExerciseFilters

S = TypeVar("S", bound="_ServiceWithSession")


class _ServiceWithSession(Protocol):
    def __init__(self, *, session: AsyncSession) -> None: ...


class CompositeServiceMixin:
    """Mixin for services that orchestrate multiple repositories.

    Provides lazy instantiation of dependent services that share
    the parent service's database session.

    Example:
        ```python
        class ExerciseService(CompositeServiceMixin, SQLAlchemyAsyncRepositoryService[m.Exercise]):
            @property
            def muscles(self) -> MuscleGroupService:
                return self._get_service(MuscleGroupService)

            async def process_exercise(self, exercise_id: UUID) -> None:
                # Accessing the cached service instance
                muscle_groups = await self.muscles.get_all()
        ```
    """

    _service_cache: dict[type, Any]

    def _get_service(self, service_cls: type[S]) -> S:
        """Get or create a dependent service instance.

        Args:
            service_cls: The service class to instantiate.

        Returns:
            Cached service instance sharing this service's session.
        """
        if not hasattr(self, "_service_cache"):
            self._service_cache = {}

        if service_cls not in self._service_cache:
            repository = cast("Any", self).repository
            self._service_cache[service_cls] = service_cls(session=repository.session)

        return cast("S", self._service_cache[service_cls])


class CacheKeyBuilder:
    """Utility for generating cache keys for complex domain-specific scenarios."""

    @classmethod
    def for_exercises(cls, params: "ExerciseFilters", user_id: "UUID") -> str:
        """Extend the filter cache key with a user ID for data isolation.

        This ensures that cached results for private or shared scopes are correctly
        partitioned between different users.
        """
        key = f"exrc_list:{params}"
        if params.scope in (ExerciseScope.USER, ExerciseScope.ALL):
            key += f":{user_id}"
        return key
