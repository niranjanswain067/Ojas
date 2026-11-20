"""
Pydantic schemas for Hybrid Search API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """An individual search hit with relevance score and source attribution."""

    chunk_id: str = Field(description="Unique chunk UUID")
    req_id: str = Field(description="Requirement identifier (e.g. REQ-001)")
    heading: str = Field(default="", description="Section heading")
    content: str = Field(description="Requirement specification text")
    score: float = Field(description="Fused Reciprocal Rank score")
    source: str = Field(description="Retrieval source: semantic, keyword, or both")
    document_id: Optional[str] = Field(default=None, description="Source document UUID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional chunk metadata")


class SearchResponse(BaseModel):
    """Response returned from hybrid search."""

    query: str
    total_results: int
    results: List[SearchResultItem]
