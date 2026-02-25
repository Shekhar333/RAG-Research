from pydantic import BaseModel, Field
from typing import List, Optional


class UploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    status: str = "indexed"


class Citation(BaseModel):
    """Citation reference with section and page information."""
    section: str
    page: int
    text_snippet: str


class QueryRequest(BaseModel):
    """Request model for querying a document."""
    document_id: str
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    """Response model for document query."""
    answer: str
    citations: List[Citation]


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    document_id: str
    section: str
    page: int
    chunk_index: int


class DocumentChunk(BaseModel):
    """Represents a chunk of text from a document."""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
