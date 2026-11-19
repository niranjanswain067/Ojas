"""
Settings API router.

Endpoints:
    GET /api/settings - Retrieve runtime settings
    PUT /api/settings - Update settings, persist to config/settings.json, trigger model reload if needed
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Set

from fastapi import APIRouter, HTTPException, status

from backend.app.config import PROJECT_ROOT, SETTINGS_PATH, get_settings
from backend.app.schemas.settings import (
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])

# Fields that necessitate a model reload if their values change
MODEL_RELOAD_FIELDS: Set[str] = {
    "model_path",
    "n_ctx",
    "n_threads",
    "n_batch",
    "n_gpu_layers",
}


def _read_settings_file() -> Dict[str, Any]:
    """Read the existing settings.json file or return defaults dict."""
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.warning("Could not parse %s: %s", SETTINGS_PATH, e)
    return get_settings().model_dump()


def _write_settings_file(data: Dict[str, Any]) -> None:
    """Save configuration to config/settings.json."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get(
    "/settings",
    response_model=SettingsResponse,
    summary="Get settings",
    description="Retrieve the current runtime configuration values.",
)
async def get_current_settings() -> SettingsResponse:
    """Return all runtime settings."""
    settings = get_settings()
    return SettingsResponse(
        model_path=settings.model_path,
        n_ctx=settings.n_ctx,
        n_threads=settings.n_threads,
        n_batch=settings.n_batch,
        n_gpu_layers=settings.n_gpu_layers,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        iteration_limit=settings.iteration_limit,
        test_timeout=settings.test_timeout,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        theme=settings.theme,
        editor_font_size=settings.editor_font_size,
    )


@router.put(
    "/settings",
    response_model=SettingsUpdateResponse,
    summary="Update settings",
    description=(
        "Update runtime settings. Changes are persisted to config/settings.json. "
        "Changes to model parameters (e.g. model_path, n_ctx, n_threads) will flag "
        "and attempt a model reload."
    ),
)
async def update_settings(updates: SettingsUpdateRequest) -> SettingsUpdateResponse:
    """Update settings and reload LLM model if required."""
    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        current = get_settings()
        return SettingsUpdateResponse(
            settings=SettingsResponse(**current.model_dump()),
            model_reload_required=False,
            model_reload_status="not_required",
            message="No settings changed.",
        )

    current_data = _read_settings_file()

    # Determine if any model-related settings actually changed
    model_reload_required = False
    for field in MODEL_RELOAD_FIELDS:
        if field in update_dict and update_dict[field] != current_data.get(field):
            model_reload_required = True
            break

    # Merge updates and save
    new_data = {**current_data, **update_dict}
    try:
        _write_settings_file(new_data)
    except Exception as e:
        logger.exception("Failed to write updated settings to %s", SETTINGS_PATH)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist settings: {e}",
        )

    # Invalidate cached settings singleton so get_settings() reloads from file
    get_settings.cache_clear()
    new_settings = get_settings()

    reload_status = "not_required"
    message = "Settings updated successfully."

    if model_reload_required:
        try:
            from backend.app.main import reload_llm_client
            loaded = reload_llm_client()
            if loaded:
                reload_status = "reloaded"
                message = "Settings saved and LLM model reloaded."
            else:
                reload_status = "error"
                message = "Settings saved, but LLM model could not be loaded."
        except Exception as e:
            logger.exception("Error during LLM reload: %s", e)
            reload_status = "error"
            message = f"Settings saved, but error reloading model: {e}"

    return SettingsUpdateResponse(
        settings=SettingsResponse(**new_settings.model_dump()),
        model_reload_required=model_reload_required,
        model_reload_status=reload_status,
        message=message,
    )

