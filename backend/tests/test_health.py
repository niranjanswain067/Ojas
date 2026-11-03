"""
Phase 5 API tests: Health endpoint.

Uses FastAPI's built-in TestClient (backed by httpx) so no running server is
needed.  The LLM model is NOT loaded during these tests — we only verify the
HTTP contract and response shape.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

# ---------------------------------------------------------------------------
# Client fixture — shared across all tests in this module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """
    Start the FastAPI app with TestClient.
    The lifespan (startup / shutdown) runs automatically, which initialises
    the database and attempts to load the LLM.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_returns_200(self, client: TestClient):
        """Health endpoint must always return HTTP 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_response_is_json(self, client: TestClient):
        """Response Content-Type must be application/json."""
        response = client.get("/api/health")
        assert "application/json" in response.headers["content-type"]

    def test_required_fields_present(self, client: TestClient):
        """All required top-level fields must be present in the response."""
        data = client.get("/api/health").json()
        required_fields = {
            "status",
            "model_loaded",
            "model_name",
            "load_time_seconds",
            "version",
            "paths",
            "last_error",
        }
        missing = required_fields - set(data.keys())
        assert not missing, f"Missing fields: {missing}"

    def test_status_is_valid_value(self, client: TestClient):
        """status must be one of the allowed literals."""
        data = client.get("/api/health").json()
        assert data["status"] in {"healthy", "degraded", "error"}

    def test_model_loaded_is_bool(self, client: TestClient):
        """model_loaded must be a boolean."""
        data = client.get("/api/health").json()
        assert isinstance(data["model_loaded"], bool)

    def test_version_field(self, client: TestClient):
        """version must be a non-empty string."""
        data = client.get("/api/health").json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_paths_subfields(self, client: TestClient):
        """paths object must contain all five sub-fields."""
        data = client.get("/api/health").json()
        paths = data.get("paths", {})
        for key in ("workspace", "models", "data", "logs", "reports"):
            assert key in paths, f"paths.{key} missing"
            assert isinstance(paths[key], str)
            assert len(paths[key]) > 0

    def test_load_time_is_number(self, client: TestClient):
        """load_time_seconds must be a non-negative number."""
        data = client.get("/api/health").json()
        assert isinstance(data["load_time_seconds"], (int, float))
        assert data["load_time_seconds"] >= 0

    def test_last_error_is_str_or_null(self, client: TestClient):
        """last_error must be either None (null) or a string."""
        data = client.get("/api/health").json()
        assert data["last_error"] is None or isinstance(data["last_error"], str)

    def test_healthy_when_model_loaded(self, client: TestClient):
        """If model_loaded is True, status should be 'healthy'."""
        data = client.get("/api/health").json()
        if data["model_loaded"]:
            assert data["status"] == "healthy"

    def test_degraded_when_model_not_loaded(self, client: TestClient):
        """If model_loaded is False, status should be 'degraded'."""
        data = client.get("/api/health").json()
        if not data["model_loaded"]:
            assert data["status"] in {"degraded", "error"}

