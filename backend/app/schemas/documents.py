"""
Pydantic schemas for requirement documents.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Metadata for an uploaded requirement document."""

    id: str = Field(description="Unique document UUID")
    project_id: str = Field(description="Associated project UUID")
    filename: str = Field(description="Original file name")
    file_type: str = Field(description="File extension type: docx, pdf, txt, md")
    file_hash: str = Field(description="SHA-256 content checksum")
    file_path: str = Field(description="Relative storage path on disk")
    status: str = Field(description="Document status: uploaded, indexing, indexed, failed")
    chunk_count: int = Field(default=0, description="Number of indexed requirement chunks")
    uploaded_at: str = Field(description="ISO-8601 upload timestamp")
    indexed_at: Optional[str] = Field(default=None, description="ISO-8601 indexing timestamp")
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    text_preview: Optional[str] = Field(default=None, description="First 200 characters of extracted text")


class DocumentUploadItem(BaseModel):
    """Result summary for an individual uploaded file."""

    id: str
    filename: str
    file_type: str
    status: str
    uploaded_at: str
    is_duplicate: bool = False
    message: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response returned upon uploading one or more files."""

    documents: List[DocumentUploadItem]
    total_uploaded: int
    skipped_duplicates: int = 0


class DocumentListResponse(BaseModel):
    """List of documents belonging to a project."""

    documents: List[DocumentResponse]
    total: int


class DocumentDetailResponse(BaseModel):
    """Full detail of a document including its parsed plain text."""

    document: DocumentResponse
    raw_text: Optional[str] = None
