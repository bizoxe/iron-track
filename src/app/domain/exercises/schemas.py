from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.config.base import get_settings
from app.domain.catalogs.schemas import (
    EquipmentRead,
    MuscleGroupRead,
    TagRead,
)
from app.domain.enums import Category, DifficultyLevel, Force, Mechanic
from app.lib.schema import (
    BasePage,
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

__all__ = (
    "ExerciseCreate",
    "ExerciseCreateSystem",
    "ExercisePage",
    "ExerciseRead",
    "ExerciseScope",
    "ExerciseUpdate",
    "ExerciseUpdateSystem",
)


FULL_CDN_PREFIX = get_settings().app.cdn_images_url_prefix

CdnRelativePath = Annotated[
    str,
    Field(
        pattern=r"^/[a-z0-9]+(?:-[a-z0-9]+)*/[^/]+\.(?:jpe?g|png|webp)$",
        max_length=512,
        description=(
            "Contract: Relative CDN path, leading '/', "
            "join: CDN_BASE_URL.rstrip('/') + path. "
            "Format: '/{exercise-directory}/{filename}.{ext}'. "
            "The first directory is the lowercase exercise name with words separated by dashes."
        ),
        examples=["/ab-roller/start.jpg", "/ab-roller/end.jpg"],
    ),
]


class ExerciseScope(StrEnum):
    """Defines the visibility and ownership scope of an exercise.

    Used to filter system exercises, user-created exercises, or both.
    """

    SYSTEM = "system"
    USER = "user"
    ALL = "all"


class ExerciseRead(CamelizedBaseStruct):
    """Complete exercise data representation for read operations."""

    id: UUID
    name: str
    created_by: UUID | None
    primary_muscles: list[MuscleGroupRead]
    secondary_muscles: list[MuscleGroupRead]
    force: str | None
    mechanic: str | None
    difficulty_level: str
    category: str
    equipment: list[EquipmentRead]
    tags: list[TagRead]
    instructions: str | None
    image_start_path: str | None
    image_end_path: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.image_start_path:
            self.image_start_path = f"{FULL_CDN_PREFIX}{self.image_start_path}"
        if self.image_end_path:
            self.image_end_path = f"{FULL_CDN_PREFIX}{self.image_end_path}"


class ExercisePage(BasePage[ExerciseRead]):
    """Cache envelope for a page of exercises."""


class ExerciseBase(CamelizedBaseSchema):
    """Base exercise schema."""

    name: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
        ),
    ]
    primary_muscles: Annotated[
        list[int],
        Field(
            min_length=1,
            description="IDs of the primary muscle groups targeted by the exercise.",
        ),
    ]
    secondary_muscles: Annotated[
        list[int],
        Field(
            default=[],
            description="IDs of the secondary muscle groups involved in the exercise.",
        ),
    ]
    force: Force | None = None
    difficulty_level: DifficultyLevel
    mechanic: Mechanic | None = None
    equipment: Annotated[
        list[int],
        Field(
            default=[],
            description="IDs of the equipment required for the exercise.",
        ),
    ]
    category: Category
    instructions: str | None = None


class ExerciseCreate(ExerciseBase):
    """User-level schema for custom exercises."""


class ExerciseCreateSystem(ExerciseBase):
    """Admin-level schema for system exercises."""

    instructions: str
    image_start_path: CdnRelativePath
    image_end_path: CdnRelativePath
    tags: Annotated[
        list[int],
        Field(
            min_length=1,
            description="IDs of the tags associated with the system exercise.",
        ),
    ]


class ExerciseUpdate(ExerciseBase):
    """User-level schema for partial updates of custom exercises."""

    name: Annotated[
        str,
        Field(
            default=None,
            min_length=3,
            max_length=100,
        ),
    ]
    primary_muscles: Annotated[
        list[int],
        Field(
            default=None,
            min_length=1,
            description=(
                "IDs of the primary muscle groups targeted by the exercise. "
                "Omit to keep unchanged; empty list is rejected for primary muscles."
            ),
        ),
    ]
    secondary_muscles: Annotated[
        list[int],
        Field(
            default=[],
            description=(
                "IDs of the secondary muscle groups involved in the exercise. "
                "Omit to keep unchanged; empty list means to clear all secondary muscles."
            ),
        ),
    ]
    difficulty_level: Annotated[DifficultyLevel, Field(default=None)]
    equipment: Annotated[
        list[int],
        Field(
            default=[],
            description=(
                "IDs of the equipment required for the exercise. "
                "Omit to keep unchanged; empty list means to clear all equipment."
            ),
        ),
    ]
    category: Annotated[Category, Field(default=None)]


class ExerciseUpdateSystem(ExerciseUpdate):
    """Admin-level schema for partial updates of system exercises."""

    instructions: Annotated[str, Field(default=None)]
    image_start_path: Annotated[CdnRelativePath, Field(default=None)]
    image_end_path: Annotated[CdnRelativePath, Field(default=None)]
    tags: Annotated[
        list[int],
        Field(
            default=None,
            min_length=1,
            description=(
                "IDs of the tags associated with the system exercise. "
                "Omit to keep unchanged; empty list is rejected for tags."
            ),
        ),
    ]
