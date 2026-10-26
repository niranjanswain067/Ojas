"""Ojas configuration loader and settings schema."""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Tuple, Type
from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"


class JsonSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that loads configuration from config/settings.json."""

    def get_field_value(
        self, field: Any, field_name: str
    ) -> Tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        if not SETTINGS_PATH.exists():
            return {}
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except Exception as e:
            logger.warning("Failed to load settings from %s: %s", SETTINGS_PATH, e)
            return {}


class OjasSettings(BaseSettings):
    """Application settings for Ojas."""

    model_config = SettingsConfigDict(
        env_prefix="OJAS_",
        case_sensitive=False,
        extra="ignore",
    )

    model_path: str = "models/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    n_ctx: int = 4096
    n_threads: int = 4
    n_batch: int = 512
    n_gpu_layers: int = 0
    max_tokens: int = 2048
    temperature: float = 0.2
    iteration_limit: int = 5
    test_timeout: int = 60
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    theme: str = "dark"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            JsonSettingsSource(settings_cls),
            file_secret_settings,
        )

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {v}")
        return v

    @field_validator("model_path")
    @classmethod
    def validate_model_path_exists(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            resolved = PROJECT_ROOT / p
        else:
            resolved = p

        if not resolved.exists():
            logger.warning(
                "Configured model path does not exist: %s (resolved: %s)",
                v,
                resolved,
            )
        return v


@lru_cache()
def get_settings() -> OjasSettings:
    """Return a singleton instance of OjasSettings."""
    return OjasSettings()
