"""
Database store for requirement documents.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.storage.db import execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def ensure_project(project_id: str, name: Optional[str] = None) -> None:
    """
    Ensure a project record exists in SQLite so foreign key constraints succeed.
    Auto-creates a project if it does not exist.
    """
    row = fetch_one("SELECT id FROM projects WHERE id = ?", (project_id,))
    if row is None:
        now = _now_iso()
        project_name = name or f"Project-{project_id[:8]}"
        try:
            execute_query(
                """
                INSERT OR IGNORE INTO projects (id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, 'created', ?, ?)
                """,
                (project_id, project_name, "Auto-created project", now, now),
            )
        except Exception as exc:
            logger.warning("Could not auto-create project %s: %s", project_id, exc)


def create_document(
    project_id: str,
    filename: str,
    file_type: str,
    file_hash: str,
    file_path: str,
    status: str = "uploaded",
    doc_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert a new document record into SQLite.
    """
    ensure_project(project_id)
    doc_uuid = doc_id or str(uuid.uuid4())
    now = _now_iso()

    execute_query(
        """
        INSERT INTO documents (
            id, project_id, filename, file_type, file_hash, file_path, status, chunk_count, uploaded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (doc_uuid, project_id, filename, file_type, file_hash, file_path, status, now),
    )

    return get_document_by_id(doc_uuid) or {
        "id": doc_uuid,
        "project_id": project_id,
        "filename": filename,
        "file_type": file_type,
        "file_hash": file_hash,
        "file_path": file_path,
        "status": status,
        "chunk_count": 0,
        "uploaded_at": now,
        "indexed_at": None,
    }


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve document by its primary key UUID."""
    return fetch_one("SELECT * FROM documents WHERE id = ?", (document_id,))


def get_document_by_filename(project_id: str, filename: str) -> Optional[Dict[str, Any]]:
    """Check if a file with this filename is already uploaded in the project."""
    return fetch_one(
        "SELECT * FROM documents WHERE project_id = ? AND filename = ?",
        (project_id, filename),
    )


def get_document_by_hash(project_id: str, file_hash: str) -> Optional[Dict[str, Any]]:
    """Find document with identical SHA-256 hash in project."""
    return fetch_one(
        "SELECT * FROM documents WHERE project_id = ? AND file_hash = ?",
        (project_id, file_hash),
    )


def list_documents(project_id: str) -> List[Dict[str, Any]]:
    """List all documents for a project, sorted newest first."""
    return fetch_all(
        "SELECT * FROM documents WHERE project_id = ? ORDER BY uploaded_at DESC",
        (project_id,),
    )


def delete_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Delete a document record from DB.
    Returns the deleted document row dict if found, or None.
    """
    doc = get_document_by_id(document_id)
    if doc is not None:
        execute_query("DELETE FROM documents WHERE id = ?", (document_id,))
    return doc


def update_document_status(
    document_id: str,
    status: str,
    chunk_count: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Update processing or indexing status for a document."""
    if chunk_count is not None:
        now = _now_iso()
        execute_query(
            "UPDATE documents SET status = ?, chunk_count = ?, indexed_at = ? WHERE id = ?",
            (status, chunk_count, now, document_id),
        )
    else:
        execute_query(
            "UPDATE documents SET status = ? WHERE id = ?",
            (status, document_id),
        )
    return get_document_by_id(document_id)
