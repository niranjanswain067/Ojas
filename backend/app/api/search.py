"""
Hybrid Search API Router.

Endpoints:
    GET /api/projects/{project_id}/search - Execute hybrid semantic + FTS5 search
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.rag.search import SearchEngine
from backend.app.schemas.search import SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["search"])


@router.get(
    "/{project_id}/search",
    response_model=SearchResponse,
    summary="Hybrid RAG Search",
    description="Execute hybrid search (dense semantic vector search + sparse FTS5 keyword search + Reciprocal Rank Fusion).",
)
async def search_requirements(
    project_id: str,
    q: str = Query(..., description="Search query text"),
    top_k: int = Query(6, ge=1, le=50, description="Maximum number of results to return"),
    collection: str = Query("requirements", description="Collection to search: requirements or code"),
) -> SearchResponse:
    """Execute hybrid search on project requirements or code chunks."""
    if not q or not q.strip():
        return SearchResponse(
            query=q,
            total_results=0,
            results=[],
        )

    try:
        engine = SearchEngine(project_id)
        hits = engine.search(
            query=q.strip(),
            top_k=top_k,
            collection=collection,
        )

        items: List[SearchResultItem] = [
            SearchResultItem(
                chunk_id=h.chunk_id,
                req_id=h.req_id,
                heading=h.heading,
                content=h.content,
                score=h.score,
                source=h.source,
                document_id=h.document_id,
                metadata=h.metadata,
            )
            for h in hits
        ]

        return SearchResponse(
            query=q,
            total_results=len(items),
            results=items,
        )
    except Exception as exc:
        logger.exception("Hybrid search error in project %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        )
