"""
Requirements API router.

Endpoints:
    GET /api/projects/{project_id}/requirements          - List indexed requirement chunks
    GET /api/projects/{project_id}/requirements/{req_id} - Get a specific requirement chunk
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.documents import ChunkResponse, RequirementListResponse
from backend.app.storage.db import fetch_all, fetch_one

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["requirements"])


@router.get(
    "/{project_id}/requirements",
    response_model=RequirementListResponse,
    summary="List requirements",
    description="List all indexed requirement chunks for a project, with optional search and document filtering.",
)
async def list_requirements(
    project_id: str,
    document_id: Optional[str] = Query(None, description="Filter by document UUID"),
    search: Optional[str] = Query(None, description="FTS keyword search query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> RequirementListResponse:
    """Retrieve indexed requirement chunks for project."""
    if search and search.strip():
        # Use FTS5 keyword search
        from backend.app.rag.index import IndexManager
        idx_mgr = IndexManager(project_id)
        rows = idx_mgr.search_fts(search.strip(), limit=limit)
    else:
        conditions = ["project_id = ?"]
        params = [project_id]

        if document_id:
            conditions.append("document_id = ?")
            params.append(document_id)

        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT * FROM chunks
        WHERE {where_clause}
        ORDER BY chunk_index ASC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        rows = fetch_all(sql, tuple(params))

    items: List[ChunkResponse] = []
    for r in rows:
        meta = json.loads(r.get("metadata") or "{}") if isinstance(r.get("metadata"), str) else (r.get("metadata") or {})
        items.append(
            ChunkResponse(
                id=r["id"],
                document_id=r["document_id"],
                project_id=r["project_id"],
                req_id=r.get("req_id") or "REQ-000",
                chunk_type=r.get("chunk_type", "requirement"),
                heading=r.get("heading") or "",
                content=r["content"],
                token_count=r.get("token_count"),
                chunk_index=r["chunk_index"],
                created_at=r["created_at"],
                metadata=meta,
            )
        )

    # Total count
    count_sql = "SELECT COUNT(*) as cnt FROM chunks WHERE project_id = ?"
    count_params = [project_id]
    if document_id:
        count_sql += " AND document_id = ?"
        count_params.append(document_id)
    total_row = fetch_one(count_sql, tuple(count_params))
    total = total_row["cnt"] if total_row else len(items)

    return RequirementListResponse(
        requirements=items,
        total=total,
    )


@router.get(
    "/{project_id}/requirements/{req_id}",
    response_model=ChunkResponse,
    summary="Get requirement by REQ-ID or Chunk ID",
    description="Retrieve a specific requirement chunk by its requirement identifier (e.g. REQ-001) or UUID.",
)
async def get_requirement(project_id: str, req_id: str) -> ChunkResponse:
    """Retrieve single requirement chunk."""
    # Try by req_id first, then by id UUID
    row = fetch_one(
        "SELECT * FROM chunks WHERE project_id = ? AND (req_id = ? OR id = ?)",
        (project_id, req_id, req_id),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement '{req_id}' not found in project '{project_id}'.",
        )

    meta = json.loads(row.get("metadata") or "{}") if isinstance(row.get("metadata"), str) else (row.get("metadata") or {})
    return ChunkResponse(
        id=row["id"],
        document_id=row["document_id"],
        project_id=row["project_id"],
        req_id=row.get("req_id") or "REQ-000",
        chunk_type=row.get("chunk_type", "requirement"),
        heading=row.get("heading") or "",
        content=row["content"],
        token_count=row.get("token_count"),
        chunk_index=row["chunk_index"],
        created_at=row["created_at"],
        metadata=meta,
    )
