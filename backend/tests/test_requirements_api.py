"""
Integration tests for Requirements API & Indexing endpoints.
"""

import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT
from backend.app.main import app
from backend.app.storage.db import init_database
from backend.app.storage.document_store import ensure_project


@pytest.fixture(autouse=True)
def setup_db():
    init_database()


@pytest.fixture
def client():
    return TestClient(app)


def test_index_single_document_and_list_requirements(client):
    project_id = f"test-req-api-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)

    # 1. Upload a document
    doc_content = b"""# Requirements Document

## REQ-PAY-01: Payment Gateway Integration
The system must process credit card transactions using Stripe API.
Failure responses must trigger automated retry up to 3 times.

## REQ-PAY-02: Invoice Generation
Upon successful payment, an itemized PDF invoice must be generated.
"""
    files = [("files", ("payment_spec.txt", doc_content, "text/plain"))]
    upload_res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["documents"][0]["id"]

    # 2. Trigger indexing of single document
    idx_res = client.post(f"/api/projects/{project_id}/documents/{doc_id}/index")
    assert idx_res.status_code == 200
    idx_data = idx_res.json()
    assert idx_data["status"] == "completed"
    assert idx_data["chunks_indexed"] >= 2

    # 3. Subsequent index without force should report already_indexed
    idx_repeat = client.post(f"/api/projects/{project_id}/documents/{doc_id}/index")
    assert idx_repeat.status_code == 200
    assert idx_repeat.json()["status"] == "already_indexed"

    # 4. List requirements
    req_res = client.get(f"/api/projects/{project_id}/requirements")
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["total"] >= 2
    req_ids = [r["req_id"] for r in req_data["requirements"]]
    assert "REQ-PAY-01" in req_ids
    assert "REQ-PAY-02" in req_ids

    # 5. Get individual requirement
    single_res = client.get(f"/api/projects/{project_id}/requirements/REQ-PAY-01")
    assert single_res.status_code == 200
    assert single_res.json()["req_id"] == "REQ-PAY-01"
    assert "Stripe" in single_res.json()["content"]

    # 6. FTS search query parameter
    search_res = client.get(f"/api/projects/{project_id}/requirements?search=invoice")
    assert search_res.status_code == 200
    assert len(search_res.json()["requirements"]) >= 1


def test_index_project_documents_sync(client):
    project_id = f"test-all-idx-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)

    # Upload document
    doc_content = b"""# Module Spec
## REQ-MOD-01: Module Architecture
All modules must be loosely coupled and communicate via standard APIs.
"""
    files = [("files", ("mod_spec.txt", doc_content, "text/plain"))]
    upload_res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert upload_res.status_code == 201

    # Index with background=false for synchronous testing
    idx_res = client.post(f"/api/projects/{project_id}/index?background=false")
    assert idx_res.status_code == 200
    assert idx_res.json()["status"] == "completed"
    assert idx_res.json()["chunks_indexed"] >= 1
