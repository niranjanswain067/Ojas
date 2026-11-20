"""
Unit tests for Ojas IndexManager (backend/app/rag/index.py).
"""

import tempfile
import uuid
import pytest

from backend.app.rag.chunker import Chunk, CodeChunk
from backend.app.rag.index import IndexManager
from backend.app.storage.db import execute_query, fetch_all, init_database
from backend.app.storage.document_store import create_document, ensure_project


@pytest.fixture(autouse=True)
def setup_db():
    init_database()


@pytest.fixture
def temp_chroma_path():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        yield tmp_dir


def test_index_document_and_fts_and_chroma(temp_chroma_path):
    project_id = f"test-idx-proj-{uuid.uuid4().hex[:6]}"
    doc_id = f"doc-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)
    create_document(
        project_id=project_id,
        filename="specs.txt",
        file_type="txt",
        file_hash="abc123hash",
        file_path="workspace/test/specs.txt",
        doc_id=doc_id,
    )

    idx_mgr = IndexManager(project_id, chroma_path=temp_chroma_path)

    chunk1 = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        project_id=project_id,
        req_id="REQ-TEST-01",
        chunk_type="requirement",
        heading="User Authentication",
        content="The system must authenticate users via encrypted tokens.",
        token_count=12,
        chunk_index=1,
        content_hash="hash1",
        created_at="2026-11-20T12:00:00",
    )
    chunk2 = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        project_id=project_id,
        req_id="REQ-TEST-02",
        chunk_type="requirement",
        heading="Password Reset",
        content="Users can request a password recovery email containing an expiring link.",
        token_count=15,
        chunk_index=2,
        content_hash="hash2",
        created_at="2026-11-20T12:00:00",
    )

    count = idx_mgr.index_document(doc_id, [chunk1, chunk2])
    assert count == 2

    # Verify SQLite rows
    db_chunks = fetch_all("SELECT * FROM chunks WHERE document_id = ?", (doc_id,))
    assert len(db_chunks) == 2

    # Verify FTS5 keyword search
    fts_results = idx_mgr.search_fts("encrypted")
    assert len(fts_results) >= 1
    assert "REQ-TEST-01" in [r["req_id"] for r in fts_results]

    fts_reset = idx_mgr.search_fts("recovery")
    assert len(fts_reset) >= 1
    assert "REQ-TEST-02" in [r["req_id"] for r in fts_reset]

    # Verify Semantic vector search
    sem_results = idx_mgr.search_semantic("log in credentials security")
    assert len(sem_results) >= 1
    assert sem_results[0]["metadata"]["project_id"] == project_id


def test_delete_document_cleans_chroma_and_sqlite(temp_chroma_path):
    project_id = f"test-del-proj-{uuid.uuid4().hex[:6]}"
    doc_id = f"doc-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)
    create_document(
        project_id=project_id,
        filename="doc.txt",
        file_type="txt",
        file_hash="hash_del",
        file_path="workspace/test/doc.txt",
        doc_id=doc_id,
    )

    idx_mgr = IndexManager(project_id, chroma_path=temp_chroma_path)
    chunk = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        project_id=project_id,
        req_id="REQ-DEL-01",
        chunk_type="requirement",
        heading="Deletion test",
        content="Content to be deleted.",
        token_count=5,
        chunk_index=1,
        content_hash="delhash",
        created_at="2026-11-20T12:00:00",
    )
    idx_mgr.index_document(doc_id, [chunk])

    assert len(fetch_all("SELECT * FROM chunks WHERE document_id = ?", (doc_id,))) == 1

    idx_mgr.delete_document(doc_id)

    assert len(fetch_all("SELECT * FROM chunks WHERE document_id = ?", (doc_id,))) == 0
    res = idx_mgr.search_semantic("Deletion test")
    matching = [r for r in res if r["metadata"].get("document_id") == doc_id]
    assert len(matching) == 0


def test_index_code(temp_chroma_path):
    project_id = f"test-code-proj-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)
    idx_mgr = IndexManager(project_id, chroma_path=temp_chroma_path)

    code_chunk = CodeChunk(
        id=str(uuid.uuid4()),
        project_id=project_id,
        file_path="src/calc.py",
        symbol_name="calculate_total",
        symbol_type="function",
        content="def calculate_total(a, b):\n    return a + b",
        start_line=1,
        end_line=2,
        content_hash="codehash",
        linked_req_ids=["REQ-CALC-01"],
        created_at="2026-11-20T12:00:00",
        updated_at="2026-11-20T12:00:00",
    )

    count = idx_mgr.index_code("src/calc.py", [code_chunk])
    assert count == 1

    db_code = fetch_all("SELECT * FROM code_chunks WHERE project_id = ?", (project_id,))
    assert len(db_code) == 1
    assert db_code[0]["symbol_name"] == "calculate_total"
