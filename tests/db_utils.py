from app.domain.exercises.schemas import (
    CategoryType,
    DifficultyLevelType,
    ForceType,
    MechanicType,
)

ENUM_MAP = {
    # ---Exercises table---
    ForceType: "force_enum",
    DifficultyLevelType: "difficulty_level_enum",
    MechanicType: "mechanic_enum",
    CategoryType: "category_enum",
}
