from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest

from app.config.constants import DEFAULT_ADMIN_EMAIL

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

    return create_app()


@pytest.fixture(scope="session", name="raw_users")
def fx_raw_users() -> list[dict[str, Any]]:
    """Unstructured user representations."""
    return [
        {
            "id": "019a536a-5d4e-7703-896d-1eaa79d993cf",
            "email": DEFAULT_ADMIN_EMAIL,
            "name": "System Administrator",
            "password": "Test_Password0!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": "019a53be-bec9-7120-81a2-8a46e85f22a4",
            "email": "superuser@example.com",
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": "019a5f0c-3a24-7693-abf4-3ed68ea9cf01",
            "email": "user@example.com",
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "019a643b-fe1e-7ae2-9fda-c45f3b77c3cb",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
        },
        {
            "id": "019a643f-5947-7110-8b7d-5b5be844de8e",
            "email": "fitness.trainer@example.com",
            "name": "Fitness Trainer",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "019a643e-db0a-77d0-89a6-0536f6d00a24",
            "email": "another@example.com",
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


@pytest.fixture(scope="session", name="custom_exercises")
def fx_custom_exercises() -> list[dict[str, Any]]:
    return [
        {
            "id": "019d1c19-0d21-78c0-809b-ec808d4e1e7b",
            "name": "Example User Exercise",
            "force": "pull",
            "difficulty_level": "intermediate",
            "mechanic": "isolation",
            "equipment": [2],
            "primary_muscles": [1],
            "secondary_muscles": [2, 3],
            "instructions": "This is a example user exercise.",
            "category": "strength",
            "created_by": "019a5f0c-3a24-7693-abf4-3ed68ea9cf01",
        },
        {
            "id": "019d1c19-0d24-7821-a465-d3487ed4c89a",
            "name": "Example User Exercise Two",
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [7],
            "primary_muscles": [12],
            "secondary_muscles": [5, 8, 6],
            "instructions": "This is a example user exercise two.",
            "category": "strength",
            "created_by": "019a5f0c-3a24-7693-abf4-3ed68ea9cf01",
        },
        {
            "id": "019d1c19-0d28-7e62-a4ab-0666afdf0a05",
            "name": "Another User's Exercise",
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [3],
            "primary_muscles": [4],
            "secondary_muscles": [10, 2],
            "instructions": "This is a another user's exercise.",
            "category": "strength",
            "created_by": "019a643e-db0a-77d0-89a6-0536f6d00a24",
        },
        {
            "id": "019d1c19-0d21-78c0-809b-ee2c5cf41b1e",
            "name": "Trail Running/Walking",
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
            "id": "019d1c19-0d24-7821-a465-d6f0a719ae95",
            "name": "Upright Row - With Bands",
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
