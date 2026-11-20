"""
Unit and integration tests for Ojas Hybrid Search Engine (backend/app/rag/search.py)
and Search API (backend/app/api/search.py).
"""

import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.rag.chunker import Chunk
from backend.app.rag.index import IndexManager
from backend.app.rag.search import SearchEngine, RRF_K
from backend.app.storage.db import init_database
from backend.app.storage.document_store import create_document, ensure_project


@pytest.fixture(autouse=True)
def setup_db():
    init_database()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def indexed_project():
    """Create a project with indexed chunks for hybrid search testing."""
    project_id = f"test-search-{uuid.uuid4().hex[:6]}"
    doc_id = f"doc-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)
    create_document(
        project_id=project_id,
        filename="library_spec.txt",
        file_type="txt",
        file_hash="hash_lib_123",
        file_path="workspace/test/library_spec.txt",
        doc_id=doc_id,
    )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as chroma_dir:
        idx_mgr = IndexManager(project_id, chroma_path=chroma_dir)

        chunks = [
            Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                project_id=project_id,
                req_id="REQ-BOOK-01",
                chunk_type="requirement",
                heading="Book Catalog Management",
                content="Librarians shall add new books to the catalog with ISBN, title, author, and genre.",
                token_count=18,
                chunk_index=1,
                content_hash="h1",
                created_at="2026-11-20T12:00:00",
            ),
            Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                project_id=project_id,
                req_id="REQ-BOOK-02",
                chunk_type="requirement",
                heading="Book Checkout",
                content="Patrons can borrow books for up to 14 days. Maximum 5 books checked out per user.",
                token_count=17,
                chunk_index=2,
                content_hash="h2",
                created_at="2026-11-20T12:00:00",
            ),
            Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                project_id=project_id,
                req_id="REQ-AUTH-01",
                chunk_type="requirement",
                heading="User Login Security",
                content="All access to the library portal requires two-factor authentication via email OTP.",
                token_count=15,
                chunk_index=3,
                content_hash="h3",
                created_at="2026-11-20T12:00:00",
            ),
        ]
        idx_mgr.index_document(doc_id, chunks)
        yield project_id, chroma_dir


def test_hybrid_search_semantic(indexed_project):
    project_id, chroma_dir = indexed_project
    engine = SearchEngine(project_id, chroma_path=chroma_dir)

    # Semantic search query: "inserting novel publications into inventory"
    results = engine.search("inserting novel publications into inventory", top_k=3)
    assert len(results) > 0
    # Should rank REQ-BOOK-01 highest because of semantic similarity to adding books
    top_req = results[0]
    assert "REQ-BOOK" in top_req.req_id
    assert top_req.score > 0.0


def test_hybrid_search_keyword(indexed_project):
    project_id, chroma_dir = indexed_project
    engine = SearchEngine(project_id, chroma_path=chroma_dir)

    # Keyword match for exact term "ISBN"
    results = engine.search("ISBN", top_k=2)
    assert len(results) > 0
    req_ids = [r.req_id for r in results]
    assert "REQ-BOOK-01" in req_ids


def test_rrf_scoring_and_source_attribution(indexed_project):
    project_id, chroma_dir = indexed_project
    engine = SearchEngine(project_id, chroma_path=chroma_dir)

    # Query with both semantic and keyword overlap: "authentication email OTP"
    results = engine.search("authentication email OTP", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert top.req_id == "REQ-AUTH-01"
    # Should have source 'both', 'semantic', or 'keyword'
    assert top.source in {"both", "semantic", "keyword"}
    assert top.score >= (1.0 / (RRF_K + 1))


def test_search_top_k_limiting(indexed_project):
    project_id, chroma_dir = indexed_project
    engine = SearchEngine(project_id, chroma_path=chroma_dir)

    results = engine.search("book library user", top_k=1)
    assert len(results) <= 1

    results_2 = engine.search("book library user", top_k=2)
    assert len(results_2) <= 2


def test_search_empty_and_gibberish(indexed_project):
    project_id, chroma_dir = indexed_project
    engine = SearchEngine(project_id, chroma_path=chroma_dir)

    # Empty query
    assert engine.search("") == []
    assert engine.search("   ") == []

    # Gibberish search
    gibberish = "xyz987qrpnonexistentterm12345"
    results = engine.search(gibberish, top_k=5)
    # Either returns empty or semantic hits with low relevance without failing
    assert isinstance(results, list)


def test_search_api_endpoint(client):
    project_id = f"test-search-api-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)

    # Upload and index a document via API
    content = b"""# Inventory API Spec
## REQ-INV-01: Stock Tracking
The warehouse tracks available stock levels in real time.
"""
    files = [("files", ("inv.txt", content, "text/plain"))]
    up_res = client.post(f"/api/projects/{project_id}/documents", files=files)
    assert up_res.status_code == 201

    idx_res = client.post(f"/api/projects/{project_id}/index?background=false")
    assert idx_res.status_code == 200

    # Execute search via API
    res = client.get(f"/api/projects/{project_id}/search?q=warehouse+stock&top_k=3")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "warehouse stock"
    assert data["total_results"] >= 1
    assert data["results"][0]["req_id"] == "REQ-INV-01"
    assert "warehouse" in data["results"][0]["content"].lower()


def test_search_api_empty_query(client):
    project_id = f"test-search-empty-{uuid.uuid4().hex[:6]}"
    ensure_project(project_id)

    res = client.get(f"/api/projects/{project_id}/search?q=")
    assert res.status_code == 200
    assert res.json()["total_results"] == 0
    assert res.json()["results"] == []
