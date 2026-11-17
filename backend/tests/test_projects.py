"""
Unit & API tests for Project CRUD operations.
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage.project_store import get_workspace_dir


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestProjectCRUD:
    """Test suite for /api/projects endpoints."""

    def test_list_projects_initially_empty_or_valid(self, client: TestClient):
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)

    def test_create_project_success(self, client: TestClient):
        payload = {
            "name": "Test Project Alpha",
            "description": "A testing project created for Phase 8.",
        }
        response = client.post("/api/projects", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project Alpha"
        assert data["description"] == "A testing project created for Phase 8."
        assert data["status"] == "idle"
        assert "id" in data
        assert data["document_count"] == 0

        # Verify workspace directory created on disk
        ws_path = get_workspace_dir(data["id"])
        assert ws_path.exists()
        assert (ws_path / "documents").exists()
        assert (ws_path / "tests").exists()

        # Clean up
        del_resp = client.delete(f"/api/projects/{data['id']}")
        assert del_resp.status_code == 204
        assert not ws_path.exists()

    def test_create_project_duplicate_name_fails(self, client: TestClient):
        name = "Unique Duplicate Test Name"
        res1 = client.post("/api/projects", json={"name": name, "description": "First"})
        assert res1.status_code == 201
        p_id = res1.json()["id"]

        try:
            # Second attempt with same name should fail (HTTP 400)
            res2 = client.post("/api/projects", json={"name": name, "description": "Second"})
            assert res2.status_code == 400
            assert "already exists" in res2.json()["detail"].lower()
        finally:
            client.delete(f"/api/projects/{p_id}")

    def test_create_project_empty_name_fails(self, client: TestClient):
        res = client.post("/api/projects", json={"name": "   ", "description": "Empty"})
        assert res.status_code in (400, 422)

    def test_get_project_by_id(self, client: TestClient):
        res = client.post("/api/projects", json={"name": "Get By ID Project"})
        assert res.status_code == 201
        p_id = res.json()["id"]

        try:
            get_res = client.get(f"/api/projects/{p_id}")
            assert get_res.status_code == 200
            p_data = get_res.json()
            assert p_data["id"] == p_id
            assert p_data["name"] == "Get By ID Project"
            assert "requirement_count" in p_data
            assert "run_count" in p_data
        finally:
            client.delete(f"/api/projects/{p_id}")

    def test_get_nonexistent_project_returns_404(self, client: TestClient):
        res = client.get("/api/projects/non-existent-uuid-12345")
        assert res.status_code == 404

    def test_patch_project_success(self, client: TestClient):
        res = client.post("/api/projects", json={"name": "Patch Me Old Name", "description": "Old desc"})
        assert res.status_code == 201
        p_id = res.json()["id"]

        try:
            patch_res = client.patch(
                f"/api/projects/{p_id}",
                json={"name": "Patch Me New Name", "description": "New updated desc"},
            )
            assert patch_res.status_code == 200
            updated = patch_res.json()
            assert updated["name"] == "Patch Me New Name"
            assert updated["description"] == "New updated desc"

            # Check partial update
            patch_res2 = client.patch(
                f"/api/projects/{p_id}",
                json={"description": "Only desc changed"},
            )
            assert patch_res2.status_code == 200
            assert patch_res2.json()["name"] == "Patch Me New Name"
            assert patch_res2.json()["description"] == "Only desc changed"
        finally:
            client.delete(f"/api/projects/{p_id}")

    def test_delete_project_cascades_and_removes_workspace(self, client: TestClient):
        res = client.post("/api/projects", json={"name": "To Be Deleted"})
        assert res.status_code == 201
        p_id = res.json()["id"]
        ws_path = get_workspace_dir(p_id)
        assert ws_path.exists()

        del_res = client.delete(f"/api/projects/{p_id}")
        assert del_res.status_code == 204

        # Verify not in DB
        get_res = client.get(f"/api/projects/{p_id}")
        assert get_res.status_code == 404

        # Verify workspace directory removed
        assert not ws_path.exists()

    def test_delete_nonexistent_project_returns_404(self, client: TestClient):
        del_res = client.delete("/api/projects/unknown-project-id-999")
        assert del_res.status_code == 404
