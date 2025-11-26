# -----------------------------------------------------------------------------
# SCRIPT: generate_exercise_fixtures.py
# DESCRIPTION: Generates the consolidated 'all_exercises.json' fixture file
#              by scanning individual exercise folders, transforming data
#              (name-to-ID mapping, slug generation, URL creation), and combining
#              the results into a single output file for database seeding.
# -----------------------------------------------------------------------------

import json
from pathlib import Path
from typing import Any

from structlog import get_logger

from src.config.base import get_settings


settings = get_settings()

logger = get_logger()

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

EXERCISES_DIR = PROJECT_ROOT_DIR / "resources" / "exercises"
FIXTURES_DIR = PROJECT_ROOT_DIR / "src" / "db" / "fixtures"
OUTPUT_FILE = PROJECT_ROOT_DIR / "src" / "db" / "fixtures" / "all_exercises.json"
BASE_IMAGES_CDN_URL = "https://raw.githubusercontent.com/bizoxe/iron-track/media/resources/exercises"


def to_snake_case(name: str) -> str:
    """Convert a name slug to snake_case.

    Replaces spaces and hyphens with underscores, and converts the string to lowercase.
    """
    return name.replace(" ", "_").replace("-", "_").lower()


def load_and_create_id_map(filename: str, lookup_key: str = "name") -> dict[str, int]:
    """Load a JSON fixture file and create a Name-to-ID map.

    Returns:
        A dictionary mapping item names to their corresponding database IDs.
    """
    filepath = FIXTURES_DIR / filename

    if not filepath.exists():
        logger.error(f"Fixture file not found: {filepath}. Cannot create ID map.")
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item[lookup_key]: item["id"] for item in data}
    except Exception as e:
        logger.error(f"Error loading or parsing fixture file {filename}: {e}")
        return {}


MUSCLE_MAP = load_and_create_id_map("muscle_groups.json")
EQUIPMENT_MAP = load_and_create_id_map("equipment.json")


def map_names_to_ids(exercise_data: dict[str, Any]) -> None:
    """Replace string names in exercise data with their corresponding IDs.

    Processes fields like 'primary_muscles', 'secondary_muscles', and 'equipment'
    to convert lists of names into lists of integer IDs based on pre-loaded maps.
    """

    def process_list_field(key: str, id_map: dict[str, int]) -> None:
        """Helper to process muscle/equipment lists."""

        value = exercise_data.get(key)

        name_list: list[str] = []
        if isinstance(value, str) and value not in ["N/A", ""]:
            name_list = [value]
        elif isinstance(value, list):
            name_list = value

        id_list: list[int] = []

        for name in name_list:
            item_id = id_map.get(name)
            if item_id is not None:
                id_list.append(item_id)
            else:
                logger.warning(
                    f"Item '{name}' not found in map for field '{key}' "
                    f"in exercise '{exercise_data.get('name', 'N/A')}'."
                )

        exercise_data[key] = id_list

    process_list_field("primary_muscles", MUSCLE_MAP)

    process_list_field("secondary_muscles", MUSCLE_MAP)

    process_list_field("equipment", EQUIPMENT_MAP)


def get_exercises_data() -> list[dict[str, Any]]:
    """Scan exercise folders, process JSON, and generate data objects.

    Reads exercise details, transforms instruction lists into single strings,
    maps muscle/equipment names to IDs, and generates image URLs and slugs.

    Returns:
        A list of exercise data dictionaries ready for database seeding.
    """
    if not MUSCLE_MAP or not EQUIPMENT_MAP:
        logger.error("Skipping exercise data generation due to missing fixture maps.")
        return []

    exercises_list: list[dict[str, Any]] = []

    try:
        subfolders = [d.name for d in EXERCISES_DIR.iterdir() if d.is_dir()]
        subfolders.sort()

    except FileNotFoundError:
        logger.error(f"Root folder '{EXERCISES_DIR}' not found. Exiting.")
        return exercises_list

    logger.info(f"Found {len(subfolders)} exercise folders to process.")

    for folder_name in subfolders:
        exercise_json_path = EXERCISES_DIR / folder_name / "exercise.json"

        if not exercise_json_path.exists():
            logger.warning(f"JSON file not found for folder: '{folder_name}'. Skipping.")
            continue

        try:
            with open(exercise_json_path, "r", encoding="utf-8") as f:
                exercise_data = json.load(f)

            instructions_list = exercise_data.get("instructions", [])
            if isinstance(instructions_list, list):
                exercise_data["instructions"] = "\n\n".join(instructions_list)

            map_names_to_ids(exercise_data)

            db_slug = to_snake_case(folder_name)

            base_url = BASE_IMAGES_CDN_URL.rstrip("/")

            image_url_start = f"{base_url}/{folder_name}/images/0.jpg"
            image_url_end = f"{base_url}/{folder_name}/images/1.jpg"

            exercise_data.update(
                {
                    "slug": db_slug,
                    "image_url_start": image_url_start,
                    "image_url_end": image_url_end,
                    "is_system_default": True,
                }
            )

            exercises_list.append(exercise_data)
            logger.debug(f"Successfully processed and added exercise: '{db_slug}'")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: '{exercise_json_path}'. Skipping.")
        except Exception as e:
            logger.error(f"Unexpected error processing '{folder_name}': {e}")

    return exercises_list


def create_json_file(exercises: list[dict[str, Any]]) -> None:
    """Write the list of processed exercises to a single output JSON file.

    Ensures the output directory exists before writing the file.
    """
    data_to_save = exercises

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully created output file: '{OUTPUT_FILE}'.")
    except IOError as e:
        logger.error(f"Error writing to output file '{OUTPUT_FILE}': {e}")


if __name__ == "__main__":
    logger.info("--- Starting Exercise Data Generation Script ---")

    all_exercises = get_exercises_data()

    if all_exercises:
        create_json_file(all_exercises)
        logger.info(f"Script finished. Total exercises processed: {len(all_exercises)}.")
        logger.info(f"Images Base URL used: {BASE_IMAGES_CDN_URL}")
    else:
        logger.warning("No exercises were successfully processed. Output file was not created.")
