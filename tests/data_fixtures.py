from datetime import UTC, datetime
from typing import Any

import pytest

from app.config import constants as conf_const
from tests import constants as test_const


@pytest.fixture(scope="session", name="raw_users")
def fx_raw_users() -> list[dict[str, Any]]:
    """Unstructured user representations."""
    return [
        {
            "id": test_const.DEFAULT_ADMIN_ID,
            "email": conf_const.DEFAULT_ADMIN_EMAIL,
            "name": "System Administrator",
            "password": "Test_Password0!",
            "is_superuser": True,
            "is_active": True,
            "role_slug": conf_const.SUPERUSER_ROLE_SLUG,
        },
        {
            "id": test_const.SUPERUSER_ID,
            "email": test_const.SUPERUSER_EMAIL,
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
            "role_slug": conf_const.SUPERUSER_ROLE_SLUG,
        },
        {
            "id": test_const.USER_EXAMPLE_ID,
            "email": test_const.USER_EXAMPLE_EMAIL,
            "name": test_const.USER_EXAMPLE_NAME,
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
            "role_slug": conf_const.DEFAULT_USER_ROLE_SLUG,
        },
        {
            "id": test_const.INACTIVE_USER_ID,
            "email": test_const.INACTIVE_USER_EMAIL,
            "name": "Inactive User",
            "password": "InactivePassword2!",
            "is_superuser": False,
            "is_active": False,
            "role_slug": conf_const.DEFAULT_USER_ROLE_SLUG,
        },
        {
            "id": test_const.FITNESS_TRAINER_ID,
            "email": test_const.FITNESS_TRAINER_EMAIL,
            "name": "Fitness Trainer",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
            "role_slug": conf_const.FITNESS_TRAINER_ROLE_SLUG,
        },
        {
            "id": test_const.ANOTHER_USER_ID,
            "email": test_const.ANOTHER_USER_EMAIL,
            "name": "Another User",
            "password": "Test_Password4!",
            "is_superuser": False,
            "is_active": True,
            "role_slug": conf_const.DEFAULT_USER_ROLE_SLUG,
        },
        {
            "id": test_const.RETIRED_USER_ID,
            "email": test_const.RETIRED_USER_EMAIL,
            "name": "Retired User",
            "password": "Test_Password5!",
            "is_superuser": False,
            "is_active": False,
            "deleted_at": datetime(2025, 1, 1, tzinfo=UTC),
            "role_slug": conf_const.DEFAULT_USER_ROLE_SLUG,
        },
    ]


@pytest.fixture(scope="session", name="exercise_samples")
def fx_exercise_samples() -> list[dict[str, Any]]:
    """Unstructured exercise representations."""
    return [
        {
            "id": test_const.USER_EXAMPLE_EXERCISE_ID,
            "name": test_const.USER_EXAMPLE_EXERCISE_NAME,
            "force": "pull",
            "difficulty_level": "intermediate",
            "mechanic": "isolation",
            "equipment": [2],
            "primary_muscles": [1],
            "secondary_muscles": [2, 3],
            "instructions": "This is a example user exercise.",
            "category": "strength",
            "created_by": test_const.USER_EXAMPLE_ID,
        },
        {
            "id": test_const.USER_EXAMPLE_EXERCISE_ID_TWO,
            "name": test_const.USER_EXAMPLE_EXERCISE_NAME_TWO,
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [7],
            "primary_muscles": [12],
            "secondary_muscles": [5, 8, 6],
            "instructions": "This is a example user exercise two.",
            "category": "strength",
            "created_by": test_const.USER_EXAMPLE_ID,
        },
        {
            "id": test_const.ANOTHER_USER_EXERCISE_ID,
            "name": test_const.ANOTHER_USER_EXERCISE_NAME,
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [3],
            "primary_muscles": [4],
            "secondary_muscles": [10, 2],
            "instructions": "This is a another user's exercise.",
            "category": "strength",
            "created_by": test_const.ANOTHER_USER_ID,
        },
        {
            "id": test_const.SYSTEM_EXERCISE_ID,
            "name": test_const.SYSTEM_EXERCISE_NAME,
            "force": None,
            "difficulty_level": "beginner",
            "mechanic": None,
            "equipment": [],
            "primary_muscles": [4],
            "secondary_muscles": [9, 10, 2],
            "instructions": "Running or hiking on trails will get the blood pumping and heart beating almost immediately. Make sure you have good shoes. While you use the muscles in your calves and buttocks to pull yourself up a hill, the knees, joints and ankles absorb the bulk of the pounding coming back down. Take smaller steps as you walk downhill, keep your knees bent to reduce the impact and slow down to avoid falling.\n\nA 150 lb person can burn over 200 calories for 30 minutes walking uphill, compared to 175 on a flat surface. If running the trail, a 150 lb person can burn well over 500 calories in 30 minutes.",
            "category": "cardio",
            "is_system_default": True,
            "image_start_path": "/trail-running-walking/0.jpg",
            "image_end_path": "/trail-running-walking/1.jpg",
            "tags": [2, 5],
        },
        {
            "id": test_const.SYSTEM_EXERCISE_ID_TWO,
            "name": test_const.SYSTEM_EXERCISE_NAME_TWO,
            "force": "pull",
            "difficulty_level": "beginner",
            "mechanic": "compound",
            "equipment": [9],
            "primary_muscles": [14],
            "secondary_muscles": [6],
            "instructions": "To begin, stand on an exercise band so that tension begins at arm's length. Grasp the handles using a pronated (palms facing your thighs) grip that is slightly less than shoulder width. The handles should be resting on top of your thighs. Your arms should be extended with a slight bend at the elbows and your back should be straight. This will be your starting position.\n\nUse your side shoulders to lift the handles as you exhale. The handles should be close to the body as you move them up. Continue to lift the handles until they nearly touches your chin. Tip: Your elbows should drive the motion. As you lift the handles, your elbows should always be higher than your forearms. Also, keep your torso stationary and pause for a second at the top of the movement.\n\nLower the handles back down slowly to the starting position. Inhale as you perform this portion of the movement.\n\nRepeat for the recommended amount of repetitions.",
            "category": "strength",
            "is_system_default": True,
            "image_start_path": "/upright-row-with-bands/0.jpg",
            "image_end_path": "/upright-row-with-bands/1.jpg",
            "tags": [1, 2],
        },
    ]
