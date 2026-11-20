"""
Integration tests for Documents API (Phase 13).
"""

import io
from pathlib import Path
import docx
import pytest
from fastapi.testclient import TestClient

from backend.app.config import PROJECT_ROOT
from backend.app.main import app
from backend.app.storage.db import execute_query


@pytest.fixture(scope="module")
def client():
    """Start the FastAPI app with TestClient."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=True)
def cleanup_project_data():
    """Clean up test project rows and workspace folder."""
    project_id = "test-doc-proj"
    yield
    # Cleanup DB
    execute_query("DELETE FROM documents WHERE project_id = ?", (project_id,))
    execute_query("DELETE FROM projects WHERE id = ?", (project_id,))

    # Cleanup disk
    target_dir = PROJECT_ROOT / "workspace" / project_id
    if target_dir.exists():
        import shutil
        shutil.rmtree(target_dir, ignore_errors=True)


def test_upload_txt_document(client: TestClient):
    """Uploading valid txt document should succeed with 201."""
    project_id = "test-doc-proj"
    content = b"REQ-101: System shall export reports as CSV."
    files = [("files", ("spec.txt", io.BytesIO(content), "text/plain"))]

    res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert res.status_code == 201
    data = res.json()

    assert data["total_uploaded"] == 1
    assert data["skipped_duplicates"] == 0
    assert len(data["documents"]) == 1
    doc_info = data["documents"][0]
    assert doc_info["filename"] == "spec.txt"
    assert doc_info["file_type"] == "txt"
    assert doc_info["status"] == "uploaded"
    assert doc_info["is_duplicate"] is False


def test_upload_docx_document(client: TestClient):
    """Uploading docx document should extract text and store file."""
    project_id = "test-doc-proj"

    # Build docx in-memory
    doc = docx.Document()
    doc.add_paragraph("REQ-201: Billing engine calculation rules.")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    files = [("files", ("billing.docx", buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert res.status_code == 201
    assert res.json()["total_uploaded"] == 1


def test_reject_unsupported_file_type(client: TestClient):
    """Attempting to upload .exe or .bin should fail with 400 Bad Request."""
    project_id = "test-doc-proj"
    files = [("files", ("malware.exe", io.BytesIO(b"\x90\x90"), "application/octet-stream"))]

    res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert res.status_code == 400
    assert "Unsupported file type" in res.json().get("detail", "")


def test_duplicate_hash_check(client: TestClient):
    """Uploading the exact same file content again should be reported as duplicate."""
    project_id = "test-doc-proj"
    content = b"Unique content for duplicate verification test."
    files1 = [("files", ("first.txt", io.BytesIO(content), "text/plain"))]

    res1 = client.post(f"/api/projects/{project_id}/documents", files=files1)
    assert res1.status_code == 201
    assert res1.json()["total_uploaded"] == 1

    # Upload same content under same or different name
    files2 = [("files", ("second.txt", io.BytesIO(content), "text/plain"))]
    res2 = client.post(f"/api/projects/{project_id}/documents", files=files2)
    assert res2.status_code == 201
    data2 = res2.json()

    assert data2["total_uploaded"] == 0
    assert data2["skipped_duplicates"] == 1
    assert data2["documents"][0]["is_duplicate"] is True
    assert "Skipped" in data2["documents"][0]["message"]


def test_list_and_get_document(client: TestClient):
    """Listing documents should show uploaded document and detail should provide raw text."""
    project_id = "test-doc-proj"
    content = b"REQ-301: Detailed user profile specifications."
    files = [("files", ("profile.txt", io.BytesIO(content), "text/plain"))]
    upload_res = client.post(f"/api/projects/{project_id}/documents", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    # List documents
    list_res = client.get(f"/api/projects/{project_id}/documents")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # Get single document detail
    detail_res = client.get(f"/api/projects/{project_id}/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["document"]["filename"] == "profile.txt"
    assert "REQ-301" in detail["raw_text"]


def test_delete_document(client: TestClient):
    """Deleting document removes it from database and deletes file from disk."""
    project_id = "test-doc-proj"
    content = b"Temporary document to be deleted."
    files = [("files", ("to_delete.txt", io.BytesIO(content), "text/plain"))]
    upload_res = client.post(f"/api/projects/{project_id}/documents", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    # Verify exists
    list_before = client.get(f"/api/projects/{project_id}/documents").json()["documents"]
    assert any(d["id"] == doc_id for d in list_before)

    # Delete
    del_res = client.delete(f"/api/projects/{project_id}/documents/{doc_id}")
    assert del_res.status_code == 204

    # Verify deleted
    list_after = client.get(f"/api/projects/{project_id}/documents").json()["documents"]
    assert not any(d["id"] == doc_id for d in list_after)

    # Verify 404 on get
    get_res = client.get(f"/api/projects/{project_id}/documents/{doc_id}")
    assert get_res.status_code == 404
