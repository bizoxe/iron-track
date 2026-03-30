from datetime import datetime
from enum import StrEnum
from re import compile as re_compile
from typing import (
    Annotated,
    Self,
)
from uuid import UUID

from pydantic import (
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from app.config.base import get_settings
from app.domain.catalogs.schemas import (
    EquipmentRead,
    ExerciseTagRead,
    MuscleGroupRead,
)
from app.lib.schema import (
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

settings = get_settings()


FULL_CDN_PREFIX = settings.app.cdn_exercises_url_prefix

SLUG_PATTERN = re_compile(r"[^a-z0-9]+")
PATH_PATTERN = r"^/[a-z0-9\-_]+(?:/[a-z0-9\-_]+)*\.(?:jpg|jpeg|png|webp)$"

StartPath = Annotated[
    str,
    Field(
        pattern=PATH_PATTERN,
        description=(
            "Path relative to the exercise folder. Must start with a slash. Used for 'start' position images. "
            "Example format: '/{exercise name}/{filename}.jpg'"
        ),
        examples=["/ab-roller/0.jpg", "/bench-press/images/start.webp"],
    ),
]
EndPath = Annotated[
    str,
    Field(
        pattern=PATH_PATTERN,
        description=(
            "Path relative to the exercise folder. Must start with a slash. Used for 'end' position images. "
            "Example format: '/{exercise name}/{filename}.jpg'"
        ),
        examples=["/ab-roller/0.jpg", "/bench-press/images/start.webp"],
    ),
]


def slugify(name: str) -> str:
    return SLUG_PATTERN.sub("-", name.lower()).strip("-")


class ExerciseScope(StrEnum):
    """Defines the visibility and ownership scope of an exercise.

    Used for filtering system-provided vs user-created content.
    """

    SYSTEM = "system"
    USER = "user"
    ALL = "all"


class DifficultyLevelType(StrEnum):
    """The perceived difficulty level of an exercise."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ForceType(StrEnum):
    """The type of force required to perform the exercise."""

    PULL = "pull"
    PUSH = "push"
    STATIC = "static"


class MechanicType(StrEnum):
    """The mechanical action of the exercise."""

    COMPOUND = "compound"
    ISOLATION = "isolation"


class CategoryType(StrEnum):
    """The primary fitness category or goal of the exercise."""

    STRENGTH = "strength"
    STRETCHING = "stretching"
    PLYOMETRICS = "plyometrics"
    STRONGMAN = "strongman"
    POWERLIFTING = "powerlifting"
    CARDIO = "cardio"
    OLYMPIC_WEIGHTLIFTING = "olympic weightlifting"


class ExerciseBase(CamelizedBaseSchema):
    """Base exercise attributes used as a blueprint for other schemas."""

    name: Annotated[
        str,
        Field(
            default=None,
            min_length=3,
            max_length=100,
            description="Unique exercise name (3-100 characters).",
        ),
    ]
    primary_muscles: Annotated[
        list[int] | None,
        Field(
            min_length=1,
            description="IDs of the **main muscle groups** targeted. Must include at least one ID.",
        ),
    ] = None
    secondary_muscles: Annotated[
        list[int] | None,
        Field(
            min_length=1,
            description="IDs of the **assisting muscle groups** involved. Must include at least one ID.",
        ),
    ] = None
    force: ForceType | None = None
    difficulty_level: DifficultyLevelType | None = None
    mechanic: MechanicType | None = None
    equipment: Annotated[
        list[int] | None,
        Field(
            min_length=1,
            description="IDs of the **equipment** required for the exercise. Must include at least one ID.",
        ),
    ] = None
    category: CategoryType | None = None
    instructions: str | None = None


class ExerciseCreate(ExerciseBase):
    """Schema for user-level exercise creation. Requires core fields."""

    name: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            description="Unique exercise name (3-100 characters).",
        ),
    ]
    primary_muscles: Annotated[
        list[int],
        Field(
            min_length=1,
            description="IDs of the **main muscle groups** targeted. Must include at least one ID.",
        ),
    ]
    difficulty_level: DifficultyLevelType
    category: CategoryType


class ExerciseCreateSystem(ExerciseCreate):
    """Admin-level schema for system exercises with specific fields."""

    image_path_start: StartPath | None = None
    image_path_end: EndPath | None = None
    instructions: str
    tags: Annotated[
        list[int],
        Field(
            min_length=1,
            description="System-defined tag IDs (e.g., equipment types, goals). Must include at least one ID.",
        ),
    ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slug(self) -> str:
        """URL-friendly identifier generated from the name."""
        return slugify(self.name)


class ExerciseUpdate(ExerciseBase):
    """Schema for partial updates of user exercises."""

    primary_muscles: Annotated[
        list[int],
        Field(
            default=None,
            min_length=1,
            description="IDs of the **main muscle groups** targeted. Must include at least one ID.",
        ),
    ]


class ExerciseUpdateSystem(ExerciseUpdate):
    """Schema for administrative updates of system exercises."""

    model_config = ConfigDict(frozen=False)

    image_path_start: StartPath | None = None
    image_path_end: EndPath | None = None
    tags: Annotated[
        list[int],
        Field(
            default=None,
            min_length=1,
            description="Updated list of system tag IDs. Must include at least one ID.",
        ),
    ]
    slug: Annotated[str | None, SkipJsonSchema()] = None

    @model_validator(mode="after")
    def generate_slug(self) -> Self:
        """Generate a new slug only if the name is being updated."""
        if self.name:
            self.slug = slugify(self.name)
            self.__pydantic_fields_set__.add("slug")
        return self


class ExerciseRead(CamelizedBaseStruct):
    """Complete exercise data representation for read operations."""

    id: UUID
    name: str
    primary_muscles: list[MuscleGroupRead]
    secondary_muscles: list[MuscleGroupRead]
    force: str | None
    difficulty_level: str
    mechanic: str | None
    equipment: list[EquipmentRead]
    category: str
    instructions: str | None
    image_path_start: str | None
    image_path_end: str | None
    tags: list[ExerciseTagRead]
    slug: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.image_path_start:
            self.image_path_start = f"{FULL_CDN_PREFIX}{self.image_path_start}"
        if self.image_path_end:
            self.image_path_end = f"{FULL_CDN_PREFIX}{self.image_path_end}"
