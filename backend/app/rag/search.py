"""
Ojas Hybrid RAG Search Engine.

Combines semantic vector search (ChromaDB + fastembed) with
BM25 keyword full-text search (SQLite FTS5), fusing results via
Reciprocal Rank Fusion (RRF).
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from backend.app.rag.embedder import get_embedder
from backend.app.rag.index import IndexManager
from backend.app.storage.db import fetch_all

logger = logging.getLogger(__name__)

# Standard Reciprocal Rank Fusion constant (Cormack et al.)
RRF_K = 60


@dataclass
class SearchResult:
    """An individual search hit returned by hybrid search."""

    chunk_id: str
    req_id: str
    heading: str
    content: str
    score: float
    source: str  # 'semantic', 'keyword', or 'both'
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "req_id": self.req_id,
            "heading": self.heading,
            "content": self.content,
            "score": round(self.score, 6),
            "source": self.source,
            "document_id": self.document_id,
            "metadata": self.metadata,
        }


class SearchEngine:
    """
    Hybrid Search Engine executing dense semantic vector retrieval
    and sparse lexical FTS5 retrieval, merged with Reciprocal Rank Fusion.
    """

    def __init__(
        self,
        project_id: str,
        chroma_path: Optional[str] = None,
    ) -> None:
        self.project_id = project_id
        self._index_mgr = IndexManager(project_id, chroma_path=chroma_path)
        self._embedder = get_embedder()

    def search(
        self,
        query: str,
        top_k: int = 6,
        collection: str = "requirements",
    ) -> List[SearchResult]:
        """
        Execute hybrid search over the specified collection:
        1. Dense semantic search via ChromaDB (retrieves top 2 * top_k).
        2. Lexical keyword search via SQLite FTS5 (retrieves top 2 * top_k).
        3. Reciprocal Rank Fusion (RRF) combining the two ranked lists.
        4. Return top_k merged results sorted by fused score.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            return []

        fetch_limit = max(top_k * 2, 10)

        # -------------------------------------------------------------------
        # 1. Semantic Search
        # -------------------------------------------------------------------
        semantic_hits: List[Dict[str, Any]] = []
        try:
            semantic_hits = self._index_mgr.search_semantic(
                clean_query,
                n_results=fetch_limit,
            )
        except Exception as exc:
            logger.warning("Semantic search failed: %s", exc)

        # -------------------------------------------------------------------
        # 2. Lexical Keyword Search (SQLite FTS5)
        # -------------------------------------------------------------------
        keyword_hits: List[Dict[str, Any]] = []
        try:
            keyword_hits = self._index_mgr.search_fts(
                clean_query,
                limit=fetch_limit,
            )
        except Exception as exc:
            logger.warning("FTS search failed: %s", exc)

        if not semantic_hits and not keyword_hits:
            return []

        # -------------------------------------------------------------------
        # 3. Reciprocal Rank Fusion (RRF)
        # -------------------------------------------------------------------
        # score(d) = sum(1.0 / (RRF_K + rank))
        rrf_scores: Dict[str, float] = {}
        doc_sources: Dict[str, Set[str]] = {}
        chunk_data: Dict[str, Dict[str, Any]] = {}

        # Process Semantic Rank List
        for rank, hit in enumerate(semantic_hits, start=1):
            c_id = hit["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (RRF_K + rank))
            if c_id not in doc_sources:
                doc_sources[c_id] = set()
            doc_sources[c_id].add("semantic")

            meta = hit.get("metadata") or {}
            chunk_data[c_id] = {
                "chunk_id": c_id,
                "req_id": meta.get("req_id") or "REQ-000",
                "heading": meta.get("heading") or "",
                "content": hit.get("content") or "",
                "document_id": meta.get("document_id"),
                "metadata": meta,
            }

        # Process Keyword Rank List
        for rank, row in enumerate(keyword_hits, start=1):
            c_id = row["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (RRF_K + rank))
            if c_id not in doc_sources:
                doc_sources[c_id] = set()
            doc_sources[c_id].add("keyword")

            # If not already populated from semantic search, populate from row
            if c_id not in chunk_data:
                meta = row.get("metadata")
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                elif not isinstance(meta, dict):
                    meta = {}

                chunk_data[c_id] = {
                    "chunk_id": c_id,
                    "req_id": row.get("req_id") or "REQ-000",
                    "heading": row.get("heading") or "",
                    "content": row.get("content") or "",
                    "document_id": row.get("document_id"),
                    "metadata": meta,
                }

        # Sort candidate IDs by fused RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        results: List[SearchResult] = []
        for c_id in sorted_ids[:top_k]:
            data = chunk_data[c_id]
            sources = doc_sources[c_id]
            source_tag = "both" if len(sources) > 1 else next(iter(sources))

            results.append(
                SearchResult(
                    chunk_id=c_id,
                    req_id=data["req_id"],
                    heading=data["heading"],
                    content=data["content"],
                    score=rrf_scores[c_id],
                    source=source_tag,
                    document_id=data["document_id"],
                    metadata=data["metadata"],
                )
            )

        return results
