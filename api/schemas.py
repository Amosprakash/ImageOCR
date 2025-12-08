# api/schemas.py
"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class OCRResponse(BaseModel):
    """Response model for OCR endpoints."""
    success: bool
    message: str
    text: str
    confidence: Optional[float] = None
    debug_images: Optional[List[str]] = None


class FieldExtractionResponse(BaseModel):
    """Response model for field extraction."""
    success: bool
    fields: Dict[str, Any]
    rows: Optional[List[Dict]] = None


class RAGIndexRequest(BaseModel):
    """Request model for RAG indexing."""
    text: str = Field(..., description="Text to index in vector store")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
    store_id: str = Field(default="default", description="Vector store identifier")


class RAGIndexResponse(BaseModel):
    """Response model for RAG indexing."""
    success: bool
    message: str
    store_id: str
    num_chunks: int


class RAGQueryRequest(BaseModel):
    """Request model for RAG querying."""
    query: str = Field(..., description="Search query")
    store_id: str = Field(default="default", description="Vector store identifier")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


class RAGQueryResponse(BaseModel):
    """Response model for RAG querying."""
    success: bool
    query: str
    chunks: List[str]
    scores: List[float]
    metadata: Dict[str, Any]


class RAGStatsResponse(BaseModel):
    """Response model for RAG statistics."""
    success: bool
    stores: List[str]
    stats: Optional[Dict[str, Any]] = None


class KnowledgeGraphRequest(BaseModel):
    """Request model for knowledge graph generation."""
    fields: Dict[str, Any] = Field(..., description="Structured fields to convert to graph")
    doc_name: str = Field(default="Document", description="Name of the document")
    export_format: str = Field(default="json", description="Export format: json or png")


class KnowledgeGraphResponse(BaseModel):
    """Response model for knowledge graph generation."""
    success: bool
    message: str
    output_path: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
