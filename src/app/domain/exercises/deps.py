from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
)

from fastapi import Depends

from app.config.app_settings import DatabaseSession  # noqa: TC001
from app.domain.exercises.services import ExerciseService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def provide_exercise_service(db_session: DatabaseSession) -> AsyncGenerator[ExerciseService, None]:
    """Provide a new, scoped instance of the ExerciseService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        ExerciseService: The new service instance.
    """
    async with ExerciseService.new(session=db_session) as service:
        yield service


ExerciseServiceDep = Annotated[ExerciseService, Depends(provide_exercise_service)]
