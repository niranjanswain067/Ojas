"""
Documents API router.

Endpoints:
    POST   /api/projects/{project_id}/documents       - Upload one or more requirement documents
    GET    /api/projects/{project_id}/documents       - List documents for a project
    GET    /api/projects/{project_id}/documents/{id}  - Get document detail and parsed text
    DELETE /api/projects/{project_id}/documents/{id}  - Delete document and remove file from disk
"""

import hashlib
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

from backend.app.config import PROJECT_ROOT
from backend.app.rag.parser import SUPPORTED_EXTENSIONS, detect_file_type, parse_document
from backend.app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadItem,
    DocumentUploadResponse,
)
from backend.app.storage import document_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["documents"])


def _get_project_doc_dir(project_id: str) -> Path:
    """Return the absolute path to workspace/<project_id>/documents/."""
    doc_dir = PROJECT_ROOT / "workspace" / project_id / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


@router.post(
    "/{project_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload requirement documents",
    description="Uploads one or more requirement documents (DOCX, PDF, TXT, MD). Computes SHA-256 and saves to workspace.",
)
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
) -> DocumentUploadResponse:
    """Upload, validate, and store requirement documents."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided in upload request.",
        )

    # 1. Validate file types first
    for f in files:
        filename = f.filename or ""
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}' for file '{filename}'. Only docx, pdf, txt, and md are supported.",
            )

    doc_dir = _get_project_doc_dir(project_id)
    uploaded_items: List[DocumentUploadItem] = []
    skipped_count = 0

    for upload_file in files:
        raw_name = upload_file.filename or "document.txt"
        filename = Path(raw_name).name or "document.txt"
        file_ext = Path(filename).suffix.lower()
        file_type = detect_file_type(filename)

        content = await upload_file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # Check for existing document with same content hash
        existing_doc = document_store.get_document_by_hash(project_id, file_hash)
        if existing_doc is not None:
            skipped_count += 1
            uploaded_items.append(
                DocumentUploadItem(
                    id=existing_doc["id"],
                    filename=existing_doc["filename"],
                    file_type=existing_doc["file_type"],
                    status=existing_doc["status"],
                    uploaded_at=existing_doc["uploaded_at"],
                    is_duplicate=True,
                    message=f"File content matches existing document '{existing_doc['filename']}'. Skipped.",
                )
            )
            continue

        # Check if filename already exists; if so, create a unique filename
        dest_path = doc_dir / filename
        if dest_path.exists():
            stem = Path(filename).stem
            dest_path = doc_dir / f"{stem}_{file_hash[:8]}{file_ext}"

        dest_path.write_bytes(content)

        # Relative path from project root for storage
        rel_path = str(dest_path.relative_to(PROJECT_ROOT)).replace("\\", "/")

        # Attempt to parse to verify content extractability
        try:
            extracted_text = parse_document(dest_path, file_type=file_type)
            logger.info("Successfully parsed uploaded document %s (%d chars)", filename, len(extracted_text))
        except Exception as exc:
            logger.warning("Document %s saved but parsing produced warning: %s", filename, exc)

        record = document_store.create_document(
            project_id=project_id,
            filename=dest_path.name,
            file_type=file_type,
            file_hash=file_hash,
            file_path=rel_path,
            status="uploaded",
        )

        uploaded_items.append(
            DocumentUploadItem(
                id=record["id"],
                filename=record["filename"],
                file_type=record["file_type"],
                status=record["status"],
                uploaded_at=record["uploaded_at"],
                is_duplicate=False,
                message="Uploaded successfully.",
            )
        )

    return DocumentUploadResponse(
        documents=uploaded_items,
        total_uploaded=len(uploaded_items) - skipped_count,
        skipped_duplicates=skipped_count,
    )


@router.get(
    "/{project_id}/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="List all requirement documents uploaded for a specific project.",
)
async def list_documents(project_id: str) -> DocumentListResponse:
    """List documents for project with indexing status and file metadata."""
    records = document_store.list_documents(project_id)
    doc_responses: List[DocumentResponse] = []

    for r in records:
        size_bytes: int | None = None
        preview: str | None = None
        file_path = PROJECT_ROOT / r["file_path"]

        if file_path.exists():
            try:
                size_bytes = file_path.stat().st_size
                text = parse_document(file_path, file_type=r["file_type"])
                preview = text[:200] if text else None
            except Exception:
                pass

        doc_responses.append(
            DocumentResponse(
                id=r["id"],
                project_id=r["project_id"],
                filename=r["filename"],
                file_type=r["file_type"],
                file_hash=r["file_hash"],
                file_path=r["file_path"],
                status=r["status"],
                chunk_count=r.get("chunk_count", 0),
                uploaded_at=r["uploaded_at"],
                indexed_at=r.get("indexed_at"),
                size_bytes=size_bytes,
                text_preview=preview,
            )
        )

    return DocumentListResponse(
        documents=doc_responses,
        total=len(doc_responses),
    )


@router.get(
    "/{project_id}/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Retrieve metadata and full parsed plain text for a document.",
)
async def get_document(project_id: str, document_id: str) -> DocumentDetailResponse:
    """Retrieve document detail and full parsed plain text."""
    doc = document_store.get_document_by_id(document_id)
    if doc is None or doc["project_id"] != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in project {project_id}.",
        )

    file_path = PROJECT_ROOT / doc["file_path"]
    raw_text: str | None = None
    size_bytes: int | None = None

    if file_path.exists():
        size_bytes = file_path.stat().st_size
        try:
            raw_text = parse_document(file_path, file_type=doc["file_type"])
        except Exception as exc:
            raw_text = f"[Error extracting text: {exc}]"

    doc_response = DocumentResponse(
        id=doc["id"],
        project_id=doc["project_id"],
        filename=doc["filename"],
        file_type=doc["file_type"],
        file_hash=doc["file_hash"],
        file_path=doc["file_path"],
        status=doc["status"],
        chunk_count=doc.get("chunk_count", 0),
        uploaded_at=doc["uploaded_at"],
        indexed_at=doc.get("indexed_at"),
        size_bytes=size_bytes,
        text_preview=raw_text[:200] if raw_text else None,
    )

    return DocumentDetailResponse(
        document=doc_response,
        raw_text=raw_text,
    )


@router.delete(
    "/{project_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Deletes a document from SQLite and removes the physical file from disk.",
)
async def delete_document(project_id: str, document_id: str):
    """Delete document and its corresponding file."""
    doc = document_store.get_document_by_id(document_id)
    if doc is None or doc["project_id"] != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in project {project_id}.",
        )

    # 1. Delete from SQLite
    document_store.delete_document(document_id)

    # 2. Delete physical file from disk
    file_path = PROJECT_ROOT / doc["file_path"]
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info("Deleted document file from disk: %s", file_path)
        except Exception as exc:
            logger.warning("Could not delete file %s from disk: %s", file_path, exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

