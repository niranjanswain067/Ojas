"""
Unit tests for Ojas Chunker module (backend/app/rag/chunker.py).
"""

import pytest

from backend.app.rag.chunker import (
    Chunk,
    CodeChunk,
    chunk_code,
    chunk_document,
    estimate_tokens,
    extract_req_ids,
)


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") >= 2
    long_text = "word " * 100
    assert estimate_tokens(long_text) >= 100


def test_extract_req_ids():
    text = "This is REQ-001 and REQ_002, also mentioned REQ-AUTH-99."
    reqs = extract_req_ids(text)
    assert "REQ-001" in reqs
    assert "REQ-002" in reqs
    assert "REQ-AUTH-99" in reqs
    # Deduplication test
    assert len(reqs) == 3


def test_chunk_document_basic():
    doc_text = """# User Authentication Specification

## REQ-AUTH-01: User Registration
Users must be able to register with email and password.
Passwords must be at least 8 characters long and contain a special symbol.

## REQ-AUTH-02: User Login
Users must be able to authenticate and receive a JWT token.
Tokens expire after 24 hours.

## General Information
System logs all login attempts for security auditing purposes.
"""
    chunks = chunk_document(doc_text, document_id="doc-1", project_id="proj-1")
    assert len(chunks) >= 2
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.project_id == "proj-1" for c in chunks)
    assert all(c.document_id == "doc-1" for c in chunks)

    # Check explicit REQ IDs
    req_ids = [c.req_id for c in chunks]
    assert "REQ-AUTH-01" in req_ids
    assert "REQ-AUTH-02" in req_ids


def test_chunk_document_sequential_req_ids():
    doc_text = """# Project Scope

## System Overview
The system processes orders and tracks shipping status across multiple regions.

## Payment Processing
Payments are processed via Stripe or PayPal with immediate confirmation emails.

## Inventory Management
Inventory counts decrease immediately when an order is authorized.
"""
    chunks = chunk_document(doc_text, document_id="doc-2", project_id="proj-1")
    assert len(chunks) >= 2
    # Should assign sequential REQ-001, REQ-002, etc.
    assert chunks[0].req_id.startswith("REQ-")
    assert chunks[1].req_id.startswith("REQ-")


def test_chunk_document_empty():
    assert chunk_document("", "doc-3", "proj-1") == []
    assert chunk_document("   \n\n  ", "doc-3", "proj-1") == []


def test_chunk_document_long_section_splitting():
    # Create a section with > 400 tokens
    paragraphs = []
    for i in range(10):
        paragraphs.append(f"Paragraph {i}: " + ("This is detailed specification content describing edge cases. " * 15))
    doc_text = "# Extensive Requirements\n\n" + "\n\n".join(paragraphs)

    chunks = chunk_document(doc_text, document_id="doc-4", project_id="proj-1", max_tokens=300)
    assert len(chunks) > 1
    # Check that chunks have part indicators or separate headings
    assert all(c.token_count <= 400 for c in chunks)


def test_chunk_code_functions_and_classes():
    code = '''"""Module docstring referring to REQ-AUTH-01."""

def authenticate_user(username: str, password_hash: str) -> bool:
    """Validate user credentials. Implements REQ-AUTH-02."""
    if not username:
        return False
    return True

class TokenManager:
    """Manages JWT creation. Covers REQ-AUTH-03."""

    def __init__(self, secret: str):
        self.secret = secret

    def create_token(self, payload: dict) -> str:
        return "fake-token"
'''
    code_chunks = chunk_code("auth/service.py", code, project_id="proj-1")
    assert len(code_chunks) >= 2
    symbols = {c.symbol_name: c for c in code_chunks}

    assert "authenticate_user" in symbols
    assert symbols["authenticate_user"].symbol_type == "function"
    assert "REQ-AUTH-02" in symbols["authenticate_user"].linked_req_ids

    assert "TokenManager" in symbols
    assert symbols["TokenManager"].symbol_type == "class"
    assert "REQ-AUTH-03" in symbols["TokenManager"].linked_req_ids


def test_chunk_code_syntax_error_fallback():
    broken_code = "def invalid_syntax( \n return ???"
    code_chunks = chunk_code("broken.py", broken_code, project_id="proj-1")
    assert len(code_chunks) == 1
    assert code_chunks[0].symbol_type == "module"
    assert code_chunks[0].content == broken_code
