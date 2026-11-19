"""
Phase 11 API tests: Settings endpoint.

Tests:
    - GET /api/settings
    - PUT /api/settings (update non-model fields)
    - PUT /api/settings (update model fields triggering reload flag)
    - PUT /api/settings (validation errors for port, temperature, theme)
"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import SETTINGS_PATH, get_settings
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    """Start the FastAPI app with TestClient."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=True)
def preserve_settings():
    """Backup config/settings.json before test and restore after."""
    backup_data = None
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            backup_data = f.read()

    yield

    if backup_data is not None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.write(backup_data)
    get_settings.cache_clear()


class TestSettingsAPI:
    """Tests for /api/settings."""

    def test_get_settings_success(self, client: TestClient):
        """GET /api/settings must return 200 with all expected config fields."""
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()

        expected_fields = {
            "model_path",
            "n_ctx",
            "n_threads",
            "n_batch",
            "n_gpu_layers",
            "max_tokens",
            "temperature",
            "iteration_limit",
            "test_timeout",
            "host",
            "port",
            "log_level",
            "theme",
            "editor_font_size",
        }
        assert expected_fields.issubset(set(data.keys()))
        assert isinstance(data["port"], int)
        assert isinstance(data["temperature"], (int, float))
        assert isinstance(data["editor_font_size"], int)

    def test_put_settings_non_model_field(self, client: TestClient):
        """Updating temperature to 0.5 should update settings.json without model reload."""
        payload = {"temperature": 0.5, "iteration_limit": 8, "editor_font_size": 16}
        response = client.put("/api/settings", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["model_reload_required"] is False
        assert data["model_reload_status"] == "not_required"
        assert data["settings"]["temperature"] == 0.5
        assert data["settings"]["iteration_limit"] == 8
        assert data["settings"]["editor_font_size"] == 16

        # Verify persisted to disk
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        assert disk_data["temperature"] == 0.5
        assert disk_data["iteration_limit"] == 8
        assert disk_data["editor_font_size"] == 16

    def test_put_settings_empty_update(self, client: TestClient):
        """Empty payload should succeed and do nothing."""
        response = client.put("/api/settings", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["model_reload_required"] is False

    def test_put_settings_model_field_triggers_reload(self, client: TestClient):
        """Changing n_ctx should set model_reload_required to True."""
        current_ctx = client.get("/api/settings").json()["n_ctx"]
        new_ctx = 2048 if current_ctx != 2048 else 4096

        response = client.put("/api/settings", json={"n_ctx": new_ctx})
        assert response.status_code == 200
        data = response.json()

        assert data["model_reload_required"] is True
        assert data["model_reload_status"] in {"reloaded", "error"}
        assert data["settings"]["n_ctx"] == new_ctx

    def test_put_settings_invalid_port(self, client: TestClient):
        """Port outside 1024-65535 should fail validation."""
        response = client.put("/api/settings", json={"port": 99999})
        assert response.status_code == 422

        response2 = client.put("/api/settings", json={"port": 80})
        assert response2.status_code == 422

    def test_put_settings_invalid_temperature(self, client: TestClient):
        """Temperature must be between 0.0 and 2.0."""
        response = client.put("/api/settings", json={"temperature": -0.5})
        assert response.status_code == 422

        response2 = client.put("/api/settings", json={"temperature": 2.5})
        assert response2.status_code == 422

    def test_put_settings_invalid_theme(self, client: TestClient):
        """Theme must be 'light', 'dark', or 'system'."""
        response = client.put("/api/settings", json={"theme": "neon-green"})
        assert response.status_code == 422

    def test_put_settings_valid_theme(self, client: TestClient):
        """Valid theme update should succeed."""
        response = client.put("/api/settings", json={"theme": "light"})
        assert response.status_code == 200
        assert response.json()["settings"]["theme"] == "light"

    def test_put_settings_invalid_editor_font_size(self, client: TestClient):
        """Editor font size outside 8-32 should fail validation."""
        response = client.put("/api/settings", json={"editor_font_size": 4})
        assert response.status_code == 422

        response2 = client.put("/api/settings", json={"editor_font_size": 48})
        assert response2.status_code == 422

