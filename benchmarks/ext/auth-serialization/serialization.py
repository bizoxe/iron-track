"""Serialization Performance Benchmarks.

This module provides comparative endpoints to measure the overhead of
Pydantic model validation vs. native msgspec.Struct serialization.
Intended for use in benchmarking environments only.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import msgspec
from fastapi import APIRouter
from pydantic import BaseModel

from app.lib.json_response import MsgSpecJSONResponse

serialization_router = APIRouter(
    tags=["Serialization"],
)


# --- SCHEMAS AND ENUMS ---


class FieldsReadStruct(msgspec.Struct):
    id: int
    name: str


class FieldsReadPydantic(BaseModel):
    id: int
    name: str


class MuscleGroupReadStruct(FieldsReadStruct):
    pass


class EquipmentReadStruct(FieldsReadStruct):
    pass


class ExerciseTagReadStruct(FieldsReadStruct):
    pass


class MuscleGroupReadPydantic(FieldsReadPydantic):
    pass


class EquipmentReadPydantic(FieldsReadPydantic):
    pass


class ExerciseTagReadPydantic(FieldsReadPydantic):
    pass


class DifficultyLevelType(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ForceType(StrEnum):
    PULL = "pull"
    PUSH = "push"
    STATIC = "static"


class MechanicType(StrEnum):
    COMPOUND = "compound"
    ISOLATION = "isolation"


class CategoryType(StrEnum):
    STRENGTH = "strength"
    STRETCHING = "stretching"
    PLYOMETRICS = "plyometrics"
    STRONGMAN = "strongman"
    POWERLIFTING = "powerlifting"
    CARDIO = "cardio"
    OLYMPIC_WEIGHTLIFTING = "olympic weightlifting"


class ExerciseReadStruct(msgspec.Struct):
    id: uuid.UUID
    name: str
    primary_muscles: list[MuscleGroupReadStruct]
    secondary_muscles: list[MuscleGroupReadStruct]
    force: str | None
    difficulty_level: str
    mechanic: str | None
    equipment: list[EquipmentReadStruct]
    category: str
    instructions: str | None
    image_path_start: str | None
    image_path_end: str | None
    tags: list[ExerciseTagReadStruct]
    slug: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ExerciseReadPydantic(BaseModel):
    id: uuid.UUID
    name: str
    primary_muscles: list[MuscleGroupReadPydantic]
    secondary_muscles: list[MuscleGroupReadPydantic]
    force: str | None
    difficulty_level: str
    mechanic: str | None
    equipment: list[EquipmentReadPydantic]
    category: str
    instructions: str | None
    image_path_start: str | None
    image_path_end: str | None
    tags: list[ExerciseTagReadPydantic]
    slug: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- DATA GENERATION ---


def generate_exercise_data(count: int = 50) -> list[dict[str, Any]]:
    data_list = []
    for i in range(count):
        item = {
            "id": uuid.uuid4(),
            "name": f"Performance Test Exercise #{i}",
            "primary_muscles": [{"id": 1, "name": "Chest"}],
            "secondary_muscles": [{"id": 2, "name": "Triceps"}, {"id": 3, "name": "Anterior Deltoid"}],
            "force": "push",
            "difficulty_level": "intermediate",
            "mechanic": "compound",
            "equipment": [{"id": 1, "name": "Barbell"}, {"id": 2, "name": "Bench"}],
            "category": "strength",
            "instructions": "Long instruction text for benchmarking: " * 10,
            "image_path_start": "/static/img/start.png",
            "image_path_end": "/static/img/end.png",
            "tags": [{"id": 1, "name": "Compound"}, {"id": 2, "name": "Bulk"}],
            "slug": f"bench-press-variant-{i}",
            "created_by": uuid.uuid4(),
            "created_at": datetime.now(tz=UTC),
            "updated_at": datetime.now(tz=UTC),
        }
        data_list.append(item)
    return data_list


raw_data = generate_exercise_data(50)

# --- MSGSPEC.STRUCT MODELS ---
MOCK_EXERCISES_STRUCT = [
    ExerciseReadStruct(
        **{k: v for k, v in item.items() if k not in ["primary_muscles", "secondary_muscles", "equipment", "tags"]},
        primary_muscles=[MuscleGroupReadStruct(**m) for m in item["primary_muscles"]],
        secondary_muscles=[MuscleGroupReadStruct(**m) for m in item["secondary_muscles"]],
        equipment=[EquipmentReadStruct(**e) for e in item["equipment"]],
        tags=[ExerciseTagReadStruct(**t) for t in item["tags"]],
    )
    for item in raw_data
]

# --- PYDANTIC MODELS ---
MOCK_EXERCISES_PYDANTIC = [
    ExerciseReadPydantic(
        **{k: v for k, v in item.items() if k not in ["primary_muscles", "secondary_muscles", "equipment", "tags"]},
        primary_muscles=[MuscleGroupReadPydantic(**m) for m in item["primary_muscles"]],
        secondary_muscles=[MuscleGroupReadPydantic(**m) for m in item["secondary_muscles"]],
        equipment=[EquipmentReadPydantic(**e) for e in item["equipment"]],
        tags=[ExerciseTagReadPydantic(**t) for t in item["tags"]],
    )
    for item in raw_data
]

# --- ENDPOINTS ---


@serialization_router.get(path="/serialization-msgspec")
async def test_msgspec() -> MsgSpecJSONResponse:
    """Direct Struct-to-JSON serialization."""
    return MsgSpecJSONResponse(content=MOCK_EXERCISES_STRUCT)


@serialization_router.get(path="/serialization-pydantic")
async def test_pydantic() -> list[ExerciseReadPydantic]:
    """Standard FastAPI response pipeline with Pydantic and Starlette JSONResponse."""
    return MOCK_EXERCISES_PYDANTIC


@serialization_router.get(path="/serialization-jsonable-encoder")
async def test_jsonable_encoder() -> MsgSpecJSONResponse:
    """Pydantic models processed via `jsonable_encoder` before `msgspec` encoding.

    Note:
        This endpoint mimics standard FastAPI behavior. It requires
        `jsonable_encoder` to convert complex Pydantic types into
        JSON-compatible primitives (dicts/lists) before passing them
        to `MsgSpecJSONResponse` for high-performance binary serialization.
    """
    return MsgSpecJSONResponse(content=MOCK_EXERCISES_PYDANTIC)
