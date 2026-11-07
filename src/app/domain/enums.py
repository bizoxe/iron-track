"""Shared domain vocabulary.

Single source of enum classes for API schemas, DB column types
(via :mod:`app.db.enums`), and tests.
"""

from enum import StrEnum


class DifficultyLevel(StrEnum):
    """Difficulty level of an exercise or training plan."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class Force(StrEnum):
    """Type of force or action involved in the exercise."""

    PULL = "pull"
    PUSH = "push"
    STATIC = "static"


class Mechanic(StrEnum):
    """Mechanical action of the exercise."""

    COMPOUND = "compound"
    ISOLATION = "isolation"


class Category(StrEnum):
    """Primary fitness category or discipline of the exercise."""

    CARDIO = "cardio"
    OLYMPIC_WEIGHTLIFTING = "olympic_weightlifting"
    POWERLIFTING = "powerlifting"
    PLYOMETRICS = "plyometrics"
    STRENGTH = "strength"
    STRETCHING = "stretching"
    STRONGMAN = "strongman"


class MuscleRole(StrEnum):
    """Role of a muscle group in an exercise."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class SharingStatus(StrEnum):
    """Visibility and access policy for a training template."""

    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class UnitExerciseMode(StrEnum):
    """Performance tracking mode for a training exercise."""

    REPS = "reps"
    TIME = "time"
    DISTANCE = "distance"
    SETS_ONLY = "sets_only"


class SessionStatus(StrEnum):
    """Lifecycle status of a training session."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
