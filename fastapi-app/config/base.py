from __future__ import annotations

import os
from dataclasses import (
    dataclass,
    field,
)
from functools import lru_cache
from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).parent.parent
TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class LogSettings:
    """Logger configuration."""

    LEVEL: int = field(default_factory=lambda: int(os.getenv("LOG_LEVEL", "20")))
    UVICORN_ACCESS_LEVEL: int = field(default_factory=lambda: int(os.getenv("UVICORN_ACCESS_LEVEL", "30")))
    UVICORN_ERROR_LEVEL: int = field(default_factory=lambda: int(os.getenv("UVICORN_ERROR_LEVEL", "20")))
    LOG_DIR: Path = field(default_factory=lambda: BASE_DIR.joinpath(os.getenv("LOG_DIR", "logs")))
    SQLALCHEMY_LEVEL: int = field(default_factory=lambda: int(os.getenv("SQLALCHEMY_LEVEL", "30")))
    """SQLAlchemy logs level."""


@dataclass
class Settings:
    log: LogSettings = field(default_factory=LogSettings)

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        if env_file.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_file, override=True)

        return Settings()


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings.from_env()
