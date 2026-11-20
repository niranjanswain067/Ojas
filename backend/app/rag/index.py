"""
Ojas Index Manager.

Coordinates hybrid storage of document requirement chunks and source code chunks:
1. SQLite relational tables (`chunks`, `code_chunks`)
2. SQLite FTS5 full-text search index (`chunks_fts`)
3. ChromaDB vector database (`requirements`, `code` collections)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.config import PROJECT_ROOT
from backend.app.rag.chunker import Chunk, CodeChunk
from backend.app.rag.embedder import get_embedder
from backend.app.storage.db import execute_query, fetch_all, fetch_one
from backend.app.storage.document_store import update_document_status

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = str(PROJECT_ROOT / "data" / "chroma")


class IndexManager:
    """
    Manages semantic and full-text indexing for a project's requirements and code.
    """

    def __init__(
        self,
        project_id: str,
        chroma_path: Optional[str] = None,
    ) -> None:
        self.project_id = project_id
        self.chroma_path = chroma_path or DEFAULT_CHROMA_PATH
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collections for requirements and code
        self.requirements_col = self._client.get_or_create_collection(
            name="requirements",
            metadata={"description": "Document requirement chunks"},
        )
        self.code_col = self._client.get_or_create_collection(
            name="code",
            metadata={"description": "AST-parsed code chunks"},
        )
        self._embedder = get_embedder()

    def index_document(self, document_id: str, chunks: List[Chunk]) -> int:
        """
        Index requirement chunks for a document:
        1. Remove old chunks for document_id from SQLite & Chroma.
        2. Insert new chunks into SQLite (FTS5 triggers automatically sync chunks_fts).
        3. Compute dense embeddings and upsert into Chroma 'requirements'.
        4. Update document status to 'indexed' with chunk_count in SQLite.
        """
        if not chunks:
            # Clear old chunks and mark document indexed with 0 chunks
            self.delete_document(document_id)
            update_document_status(document_id, status="indexed", chunk_count=0)
            return 0

        # Step 1: Remove existing chunks for this document
        self.delete_document(document_id)

        # Step 2: Insert into SQLite chunks table
        for chunk in chunks:
            execute_query(
                """
                INSERT INTO chunks (
                    id, document_id, project_id, req_id, chunk_type, heading,
                    content, token_count, chunk_index, content_hash, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.project_id,
                    chunk.req_id,
                    chunk.chunk_type,
                    chunk.heading,
                    chunk.content,
                    chunk.token_count,
                    chunk.chunk_index,
                    chunk.content_hash,
                    json.dumps(chunk.metadata),
                    chunk.created_at,
                ),
            )

        # Step 3: Embed chunk texts
        texts = [f"{c.heading}\n{c.content}" if c.heading else c.content for c in chunks]
        embeddings = self._embedder.embed_texts(texts)

        # Step 4: Upsert into Chroma
        ids = [c.id for c in chunks]
        metadatas = [
            {
                "project_id": c.project_id,
                "document_id": c.document_id,
                "req_id": c.req_id,
                "heading": c.heading or "",
                "chunk_index": c.chunk_index,
                "token_count": c.token_count,
            }
            for c in chunks
        ]
        documents = [c.content for c in chunks]

        try:
            self.requirements_col.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(
                "Indexed %d chunks in Chroma for document %s (project %s)",
                len(chunks),
                document_id,
                self.project_id,
            )
        except Exception as exc:
            logger.exception("Failed to upsert chunks into Chroma: %s", exc)

        # Step 5: Update document status
        update_document_status(document_id, status="indexed", chunk_count=len(chunks))
        return len(chunks)

    def delete_document(self, document_id: str) -> None:
        """
        Delete all indexed chunks for a document from SQLite and Chroma.
        """
        # Delete from Chroma
        try:
            self.requirements_col.delete(where={"document_id": document_id})
        except Exception as exc:
            logger.debug("Could not delete document %s from Chroma: %s", document_id, exc)

        # Delete from SQLite
        execute_query("DELETE FROM chunks WHERE document_id = ?", (document_id,))

    def index_code(self, file_path: str, code_chunks: List[CodeChunk]) -> int:
        """
        Index AST code chunks for a source file into SQLite and Chroma.
        """
        # Step 1: Remove old code chunks for this file
        try:
            self.code_col.delete(
                where={"$and": [{"project_id": self.project_id}, {"file_path": file_path}]}
            )
        except Exception:
            try:
                self.code_col.delete(where={"file_path": file_path})
            except Exception:
                pass

        execute_query(
            "DELETE FROM code_chunks WHERE project_id = ? AND file_path = ?",
            (self.project_id, file_path),
        )

        if not code_chunks:
            return 0

        # Step 2: Insert into SQLite
        for chunk in code_chunks:
            execute_query(
                """
                INSERT INTO code_chunks (
                    id, project_id, file_path, symbol_name, symbol_type,
                    content, start_line, end_line, content_hash, linked_req_ids,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    chunk.project_id,
                    chunk.file_path,
                    chunk.symbol_name,
                    chunk.symbol_type,
                    chunk.content,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.content_hash,
                    json.dumps(chunk.linked_req_ids),
                    chunk.created_at,
                    chunk.updated_at,
                ),
            )

        # Step 3: Embed and upsert into Chroma
        texts = [f"# {c.symbol_type}: {c.symbol_name}\n{c.content}" for c in code_chunks]
        embeddings = self._embedder.embed_texts(texts)

        ids = [c.id for c in code_chunks]
        metadatas = [
            {
                "project_id": c.project_id,
                "file_path": c.file_path,
                "symbol_name": c.symbol_name,
                "symbol_type": c.symbol_type,
                "start_line": c.start_line,
                "end_line": c.end_line,
            }
            for c in code_chunks
        ]
        documents = [c.content for c in code_chunks]

        try:
            self.code_col.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            logger.exception("Failed to upsert code chunks into Chroma: %s", exc)

        return len(code_chunks)

    def rebuild_chroma(self) -> int:
        """
        Re-read all chunks from SQLite for project_id, re-embed, and re-populate Chroma.
        Useful when vector index needs to be rebuilt from source of truth.
        """
        rows = fetch_all(
            "SELECT * FROM chunks WHERE project_id = ? ORDER BY chunk_index ASC",
            (self.project_id,),
        )
        if not rows:
            return 0

        chunks: List[Chunk] = []
        for r in rows:
            chunks.append(
                Chunk(
                    id=r["id"],
                    document_id=r["document_id"],
                    project_id=r["project_id"],
                    req_id=r.get("req_id") or "",
                    chunk_type=r["chunk_type"],
                    heading=r.get("heading") or "",
                    content=r["content"],
                    token_count=r.get("token_count") or 0,
                    chunk_index=r["chunk_index"],
                    content_hash=r["content_hash"],
                    metadata=json.loads(r.get("metadata") or "{}"),
                    created_at=r["created_at"],
                )
            )

        # Clear Chroma collection for this project
        try:
            self.requirements_col.delete(where={"project_id": self.project_id})
        except Exception:
            pass

        texts = [f"{c.heading}\n{c.content}" if c.heading else c.content for c in chunks]
        embeddings = self._embedder.embed_texts(texts)

        ids = [c.id for c in chunks]
        metadatas = [
            {
                "project_id": c.project_id,
                "document_id": c.document_id,
                "req_id": c.req_id,
                "heading": c.heading or "",
                "chunk_index": c.chunk_index,
                "token_count": c.token_count,
            }
            for c in chunks
        ]
        documents = [c.content for c in chunks]

        self.requirements_col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Rebuilt Chroma collection for project %s with %d chunks", self.project_id, len(chunks))
        return len(chunks)

    def search_semantic(
        self,
        query: str,
        n_results: int = 5,
        req_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector similarity search in Chroma."""
        query_emb = self._embedder.embed_single(query)
        where_filter: Dict[str, Any] = {"project_id": self.project_id}
        if req_id_filter:
            where_filter = {
                "$and": [
                    {"project_id": self.project_id},
                    {"req_id": req_id_filter},
                ]
            }

        try:
            res = self.requirements_col.query(
                query_embeddings=[query_emb],
                n_results=n_results,
                where=where_filter,
            )
        except Exception as exc:
            logger.warning("Chroma search error: %s", exc)
            return []

        results: List[Dict[str, Any]] = []
        if res and res.get("ids") and res["ids"][0]:
            ids = res["ids"][0]
            distances = res["distances"][0] if res.get("distances") else [0.0] * len(ids)
            docs = res["documents"][0] if res.get("documents") else [""] * len(ids)
            metas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(ids)

            for i in range(len(ids)):
                results.append({
                    "id": ids[i],
                    "content": docs[i],
                    "distance": distances[i],
                    "metadata": metas[i],
                })
        return results

    def search_fts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text keyword search using SQLite FTS5 table `chunks_fts`.
        """
        # Sanitize query for FTS5 (avoid syntax errors on special characters)
        safe_query = '"' + query.replace('"', '""') + '"'
        sql = """
        SELECT c.*, rank
        FROM chunks c
        JOIN chunks_fts ON c.rowid = chunks_fts.rowid
        WHERE chunks_fts MATCH ? AND c.project_id = ?
        ORDER BY rank
        LIMIT ?
        """
        try:
            return fetch_all(sql, (safe_query, self.project_id, limit))
        except Exception as exc:
            logger.warning("FTS search error with query '%s': %s", query, exc)
            # Fallback to simple LIKE
            like_sql = """
            SELECT * FROM chunks
            WHERE project_id = ? AND (content LIKE ? OR heading LIKE ? OR req_id LIKE ?)
            LIMIT ?
            """
            pattern = f"%{query}%"
            return fetch_all(like_sql, (self.project_id, pattern, pattern, pattern, limit))
