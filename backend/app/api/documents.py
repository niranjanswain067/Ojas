"""
Documents API router.

Endpoints:
    POST   /api/projects/{project_id}/documents              - Upload one or more requirement documents
    GET    /api/projects/{project_id}/documents              - List documents for a project
    GET    /api/projects/{project_id}/documents/{id}         - Get document detail and parsed text
    DELETE /api/projects/{project_id}/documents/{id}         - Delete document and remove file from disk
    POST   /api/projects/{project_id}/documents/{id}/index   - Index a specific document
    POST   /api/projects/{project_id}/index                  - Index all unindexed documents in project
"""

import hashlib
import logging
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from backend.app.config import PROJECT_ROOT
from backend.app.events.event_bus import get_event_bus
from backend.app.rag.chunker import chunk_document
from backend.app.rag.index import IndexManager
from backend.app.rag.parser import SUPPORTED_EXTENSIONS, detect_file_type, parse_document
from backend.app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadItem,
    DocumentUploadResponse,
    IndexTriggerResponse,
)
from backend.app.storage import document_store
from backend.app.tasks.task_manager import get_task_manager

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
        filename = upload_file.filename or "document.txt"
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
        size_bytes: Optional[int] = None
        preview: Optional[str] = None
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
    raw_text: Optional[str] = None
    size_bytes: Optional[int] = None

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
    description="Deletes a document from SQLite and removes the physical file from disk and Chroma index.",
)
async def delete_document(project_id: str, document_id: str):
    """Delete document, its chunks from Chroma and SQLite, and its file."""
    doc = document_store.get_document_by_id(document_id)
    if doc is None or doc["project_id"] != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in project {project_id}.",
        )

    # 1. Delete chunks from Chroma and SQLite
    try:
        idx_mgr = IndexManager(project_id)
        idx_mgr.delete_document(document_id)
    except Exception as exc:
        logger.warning("Error deleting Chroma index for document %s: %s", document_id, exc)

    # 2. Delete from SQLite
    document_store.delete_document(document_id)

    # 3. Delete physical file from disk
    file_path = PROJECT_ROOT / doc["file_path"]
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info("Deleted document file from disk: %s", file_path)
        except Exception as exc:
            logger.warning("Could not delete file %s from disk: %s", file_path, exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/documents/{document_id}/index",
    response_model=IndexTriggerResponse,
    summary="Index single document",
    description="Parse, chunk, embed, and index a single document into SQLite and Chroma.",
)
async def index_single_document(
    project_id: str,
    document_id: str,
    force: bool = Query(False, description="Force re-indexing even if already indexed"),
) -> IndexTriggerResponse:
    """Parse and index a single document."""
    doc = document_store.get_document_by_id(document_id)
    if doc is None or doc["project_id"] != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in project {project_id}.",
        )

    file_path = PROJECT_ROOT / doc["file_path"]
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file {doc['filename']} does not exist on disk.",
        )

    # Check if already indexed and not forcing
    if doc["status"] == "indexed" and not force:
        return IndexTriggerResponse(
            status="already_indexed",
            message=f"Document '{doc['filename']}' is already indexed with {doc.get('chunk_count', 0)} chunks.",
            chunks_indexed=doc.get("chunk_count", 0),
            documents_processed=0,
        )

    try:
        # 1. Parse text
        text = parse_document(file_path, file_type=doc["file_type"])
        # 2. Chunk text
        chunks = chunk_document(text, document_id=document_id, project_id=project_id)
        # 3. Index into SQLite and Chroma
        idx_mgr = IndexManager(project_id)
        count = idx_mgr.index_document(document_id, chunks)

        return IndexTriggerResponse(
            status="completed",
            message=f"Successfully indexed '{doc['filename']}' into {count} requirement chunks.",
            chunks_indexed=count,
            documents_processed=1,
        )
    except Exception as exc:
        logger.exception("Failed to index document %s: %s", document_id, exc)
        document_store.update_document_status(document_id, status="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {exc}",
        )


def _background_index_job(project_id: str, run_id: str, force: bool = False) -> None:
    """Worker function executed in TaskManager background thread."""
    event_bus = get_event_bus()
    task_mgr = get_task_manager()
    docs = document_store.list_documents(project_id)
    idx_mgr = IndexManager(project_id)

    total_chunks = 0
    docs_processed = 0

    event_bus.publish(run_id, "stage_change", {"stage": "indexing", "message": "Starting document indexing…"})

    for doc in docs:
        if task_mgr.is_cancelled(run_id):
            logger.info("Indexing cancelled for run %s", run_id)
            event_bus.publish(run_id, "cancelled", {"message": "Indexing operation was cancelled"})
            return

        # Skip already indexed unless forced
        if doc["status"] == "indexed" and not force:
            continue

        file_path = PROJECT_ROOT / doc["file_path"]
        if not file_path.exists():
            continue

        event_bus.publish(
            run_id,
            "indexing_file",
            {"document_id": doc["id"], "filename": doc["filename"]},
        )

        try:
            document_store.update_document_status(doc["id"], status="indexing")
            text = parse_document(file_path, file_type=doc["file_type"])
            chunks = chunk_document(text, document_id=doc["id"], project_id=project_id)
            count = idx_mgr.index_document(doc["id"], chunks)
            total_chunks += count
            docs_processed += 1

            event_bus.publish(
                run_id,
                "file_indexed",
                {"document_id": doc["id"], "filename": doc["filename"], "chunk_count": count},
            )
        except Exception as exc:
            logger.exception("Error indexing %s: %s", doc["filename"], exc)
            document_store.update_document_status(doc["id"], status="failed")
            event_bus.publish(
                run_id,
                "error",
                {"document_id": doc["id"], "filename": doc["filename"], "error": str(exc)},
            )

    event_bus.publish(
        run_id,
        "done",
        {
            "stage": "completed",
            "documents_processed": docs_processed,
            "total_chunks": total_chunks,
            "message": f"Indexing complete: {total_chunks} requirements indexed across {docs_processed} documents.",
        },
    )


@router.post(
    "/{project_id}/index",
    response_model=IndexTriggerResponse,
    summary="Index all project documents",
    description="Index all uploaded or modified requirement documents in the project.",
)
async def index_project_documents(
    project_id: str,
    force: bool = Query(False, description="Force re-indexing all documents"),
    background: bool = Query(True, description="Run in background via TaskManager"),
) -> IndexTriggerResponse:
    """Index all unindexed or modified documents in the project."""
    docs = document_store.list_documents(project_id)
    if not docs:
        return IndexTriggerResponse(
            status="completed",
            message="No documents uploaded in this project.",
            chunks_indexed=0,
            documents_processed=0,
        )

    eligible_docs = [d for d in docs if d["status"] != "indexed" or force]
    if not eligible_docs:
        # All already indexed
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
        return IndexTriggerResponse(
            status="already_indexed",
            message=f"All {len(docs)} documents are already indexed ({total_chunks} total chunks).",
            chunks_indexed=total_chunks,
            documents_processed=0,
        )

    task_mgr = get_task_manager()

    if background:
        if task_mgr.is_busy():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A background task is already executing. Please wait or cancel it.",
            )

        run_id = f"index-{uuid.uuid4().hex[:8]}"
        submitted = task_mgr.submit(run_id, _background_index_job, project_id, run_id, force)
        if not submitted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not schedule indexing background task.",
            )

        return IndexTriggerResponse(
            status="queued",
            message=f"Indexing job queued for {len(eligible_docs)} documents.",
            task_id=run_id,
            documents_processed=len(eligible_docs),
        )
    else:
        # Synchronous execution
        run_id = f"index-sync-{uuid.uuid4().hex[:8]}"
        _background_index_job(project_id, run_id, force)
        total_chunks = sum(d.get("chunk_count", 0) for d in document_store.list_documents(project_id))
        return IndexTriggerResponse(
            status="completed",
            message=f"Successfully indexed {len(eligible_docs)} documents.",
            chunks_indexed=total_chunks,
            documents_processed=len(eligible_docs),
        )
