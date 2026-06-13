from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest

from app.config.base import get_settings
from tests import constants as c

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.anyio


@pytest.fixture(name="app")
def fx_app(
    pytestconfig: pytest.Config,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """Create and configure the FastAPI application for testing.

    Returns:
        FastAPI: The configured application instance.
    """
    from app.server.core import create_app

    monkeypatch.setattr("app.server.core.configure_logging", lambda: None)
    return create_app()


@pytest.fixture(scope="session", name="raw_users")
def fx_raw_users() -> list[dict[str, Any]]:
    """Unstructured user representations."""
    return [
        {
            "id": c.DEFAULT_ADMIN_ID,
            "email": get_settings().app.DEFAULT_ADMIN_EMAIL,
            "name": "System Administrator",
            "password": "Test_Password0!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": c.SUPERUSER_ID,
            "email": c.SUPERUSER_EMAIL,
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": c.USER_EXAMPLE_ID,
            "email": c.USER_EXAMPLE_EMAIL,
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": c.INACTIVE_USER_ID,
            "email": c.INACTIVE_USER_EMAIL,
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
        },
        {
            "id": c.FITNESS_TRAINER_ID,
            "email": c.FITNESS_TRAINER_EMAIL,
            "name": "Fitness Trainer",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": c.ANOTHER_USER_ID,
            "email": c.ANOTHER_USER_EMAIL,
            "name": "Another User",
            "password": "Test_Password4!",
            "is_superuser": False,
            "is_active": True,
        },
    ]


@pytest.fixture(scope="session", name="db_fixtures_path")
def fx_db_fixtures_path() -> Path:
    """Return the absolute path to the directory containing test-specific data."""
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session", name="exercise_samples")
def fx_exercise_samples() -> list[dict[str, Any]]:
    return [
        {
            "id": c.USER_EXEMPLE_EXERCISE_ID,
            "name": c.USER_EXEMPLE_EXERCISE_NAME,
            "force": "pull",
            "difficulty_level": "intermediate",
            "mechanic": "isolation",
            "equipment": [2],
            "primary_muscles": [1],
            "secondary_muscles": [2, 3],
            "instructions": "This is a example user exercise.",
            "category": "strength",
            "created_by": c.USER_EXAMPLE_ID,
        },
        {
            "id": c.USER_EXEMPLE_EXERCISE_ID_TWO,
            "name": c.USER_EXEMPLE_EXERCISE_NAME_TWO,
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [7],
            "primary_muscles": [12],
            "secondary_muscles": [5, 8, 6],
            "instructions": "This is a example user exercise two.",
            "category": "strength",
            "created_by": c.USER_EXAMPLE_ID,
        },
        {
            "id": c.ANOTHER_USER_EXERCISE_ID,
            "name": c.ANOTHER_USER_EXERCISE_NAME,
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [3],
            "primary_muscles": [4],
            "secondary_muscles": [10, 2],
            "instructions": "This is a another user's exercise.",
            "category": "strength",
            "created_by": c.ANOTHER_USER_ID,
        },
        {
            "id": c.SYSTEM_EXERCISE_ID,
            "name": c.SYSTEM_EXERCISE_NAME,
            "slug": "trail-running-walking",
            "force": None,
            "difficulty_level": "beginner",
            "mechanic": None,
            "equipment": [],
            "primary_muscles": [4],
            "secondary_muscles": [9, 10, 2],
            "instructions": "Running or hiking on trails will get the blood pumping and heart beating almost immediately. Make sure you have good shoes. While you use the muscles in your calves and buttocks to pull yourself up a hill, the knees, joints and ankles absorb the bulk of the pounding coming back down. Take smaller steps as you walk downhill, keep your knees bent to reduce the impact and slow down to avoid falling.\n\nA 150 lb person can burn over 200 calories for 30 minutes walking uphill, compared to 175 on a flat surface. If running the trail, a 150 lb person can burn well over 500 calories in 30 minutes.",
            "category": "cardio",
            "is_system_default": True,
            "image_path_start": "/trail-running-walking/images/0.jpg",
            "image_path_end": "/trail-running-walking/images/1.jpg",
            "tags": [2, 5],
        },
        {
            "id": c.SYSTEM_EXERCISE_ID_TWO,
            "name": c.SYSTEM_EXERCISE_NAME_TWO,
            "slug": "upright-row-with-bands",
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [9],
            "primary_muscles": [14],
            "secondary_muscles": [6],
            "instructions": "To begin, stand on an exercise band so that tension begins at arm's length. Grasp the handles using a pronated (palms facing your thighs) grip that is slightly less than shoulder width. The handles should be resting on top of your thighs. Your arms should be extended with a slight bend at the elbows and your back should be straight. This will be your starting position.\n\nUse your side shoulders to lift the handles as you exhale. The handles should be close to the body as you move them up. Continue to lift the handles until they nearly touches your chin. Tip: Your elbows should drive the motion. As you lift the handles, your elbows should always be higher than your forearms. Also, keep your torso stationary and pause for a second at the top of the movement.\n\nLower the handles back down slowly to the starting position. Inhale as you perform this portion of the movement.\n\nRepeat for the recommended amount of repetitions.",
            "category": "strength",
            "is_system_default": True,
            "image_path_start": "/upright-row-with-bands/images/0.jpg",
            "image_path_end": "/upright-row-with-bands/images/1.jpg",
            "tags": [1, 2],
        },
    ]
