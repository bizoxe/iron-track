# ruff: noqa: C901, PLR0912, PLR0915
import json
from pathlib import Path
from typing import Any

from structlog import get_logger

APP_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = APP_DIR / "db" / "fixtures"
INPUT_FILE = FIXTURES_DIR / "all_exercises.json"
OUTPUT_FILE = FIXTURES_DIR / "all_exercises_with_tags.json"
TAGS_FIXTURE = FIXTURES_DIR / "exercise_tags.json"

logger = get_logger()


def load_tags_map() -> dict[str, int]:
    with TAGS_FIXTURE.open(encoding="utf-8") as f:
        data = json.load(f)
        return {item["name"]: item["id"] for item in data}


def suggest_tag_ids(exercise: dict[str, Any], tags_map: dict[str, int]) -> list[int]:
    tag_ids = set()
    name = exercise.get("name", "").lower()
    instructions = exercise.get("instructions", "").lower()
    category = exercise.get("category", "").lower()
    equipment_ids = exercise.get("equipment", [])
    muscle_ids = exercise.get("primary_muscles", []) + exercise.get("secondary_muscles", [])

    def add_tag(tag_name: str) -> None:
        if tag_id := tags_map.get(tag_name):
            tag_ids.add(tag_id)

    # ---  Laterality ---
    uni_patterns = ["single-arm", "single-leg", "one arm", "one leg", "each leg", "each arm", "alternating"]
    if any(p in name or p in instructions for p in uni_patterns):
        add_tag("unilateral")
    else:
        add_tag("bilateral")

    # --- Body position ---
    is_hanging = "hang" in instructions or "hanging" in name
    is_seated = any(k in instructions for k in ["seated", "sit on", "sitting", "on a bench", "on the bench"])
    is_lying = any(k in instructions for k in ["lying", "lay on", "on your back", "on your stomach", "supine", "prone"])

    if not is_seated:
        is_lying = is_lying or "floor" in instructions

    if is_hanging:
        add_tag("hanging")
    elif is_seated:
        add_tag("seated")
    elif is_lying:
        add_tag("lying")
    elif any(k in instructions for k in ["standing", "stand up", "upright"]):
        add_tag("standing")

    # --- Therapy and Posture ---
    pro_sports = {"strongman", "powerlifting", "olympic weightlifting"}
    if category not in pro_sports:
        rehab_muscles = {11, 16}  # lower back, neck
        if any(mid in rehab_muscles for mid in muscle_ids) or "posture" in instructions:
            add_tag("rehab")
            add_tag("posture correction")

    # --- Nature of Load ---
    if "static hold" in instructions or (
        "hold" in instructions and "seconds" in instructions and "reps" not in instructions
    ):
        add_tag("isometric")

    if category in ["plyometrics", "strongman", "powerlifting"] or "explosive" in instructions:
        add_tag("explosive")
        add_tag("high impact")

    # --- Location ---
    home_equip = {1, 5, 6, 9, 11}
    if any(eid in home_equip for eid in equipment_ids):
        add_tag("home friendly")
        add_tag("travel friendly")

    if not any(eid in {2, 8, 12} for eid in equipment_ids):
        add_tag("outdoor")

    # --- Patterns and functionality ---
    if "squat" in name or ("squat" in instructions and "reps" in instructions):
        add_tag("squat pattern")
    if any(k in name or k in instructions for k in ["deadlift", "hinge", "kettlebell swing"]):
        add_tag("hinge pattern")

    if 1 in muscle_ids or "core" in name:
        add_tag("core stability")
        add_tag("activation")
        add_tag("balance")

    if category == "stretching":
        add_tag("mobility")
        add_tag("warm-up")
        add_tag("cool-down")

    return sorted(tag_ids)


def main() -> None:
    tags_map = load_tags_map()
    with INPUT_FILE.open(encoding="utf-8") as f:
        exercises = json.load(f)

    for ex in exercises:
        ex["tags"] = suggest_tag_ids(ex, tags_map)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)

    enriched = sum(1 for ex in exercises if ex["tags"])
    logger.info(
        "exercises_processed_successfully",
        exrecises=len(exercises),
        enriched=enriched,
    )


if __name__ == "__main__":
    main()
