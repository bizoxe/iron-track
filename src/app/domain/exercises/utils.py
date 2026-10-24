from __future__ import annotations

from re import compile as re_compile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.exercise import Exercise
    from app.domain.accounts.schemas import UserAuth

_SLUG_PATTERN = re_compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_PATTERN.sub("-", name.lower()).strip("-")


def can_access_exercise(
    exercise: Exercise,
    user: UserAuth,
) -> bool:
    return exercise.is_system_default or exercise.created_by == user.id


def can_delete_exercise(
    exercise: Exercise,
    user: UserAuth,
) -> bool:
    return not exercise.is_system_default and exercise.created_by == user.id
