from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
)

from fastapi import Depends

from app.config.app_settings import DatabaseSession  # noqa: TC001
from app.domain.catalogs.services import (
    EquipmentService,
    ExerciseTagService,
    MuscleGroupService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def provide_muscle_group_service(db_session: DatabaseSession) -> AsyncGenerator[MuscleGroupService, None]:
    """Provide a new, scoped instance of the MuscleGroupService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        MuscleGroupService: The new service instance.
    """
    async with MuscleGroupService.new(session=db_session) as service:
        yield service


async def provide_equipment_service(db_session: DatabaseSession) -> AsyncGenerator[EquipmentService, None]:
    """Provide a new, scoped instance of the EquipmentService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        EquipmentService: The new service instance.
    """
    async with EquipmentService.new(session=db_session) as service:
        yield service


async def provide_exercise_tag_service(db_session: DatabaseSession) -> AsyncGenerator[ExerciseTagService, None]:
    """Provide a new, scoped instance of the ExerciseTagService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        ExerciseTagService: The new service instance.
    """
    async with ExerciseTagService.new(session=db_session) as service:
        yield service


MuscleGroupDep = Annotated[MuscleGroupService, Depends(provide_muscle_group_service)]
EquipmentDep = Annotated[EquipmentService, Depends(provide_equipment_service)]
ExerciseTagDep = Annotated[ExerciseTagService, Depends(provide_exercise_tag_service)]
