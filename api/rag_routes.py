# api/rag_routes.py
"""
RAG API routes for ImageAI.
Handles vector store indexing, querying, and management.
"""
from fastapi import APIRouter, HTTPException
from api.schemas import (
    RAGIndexRequest, RAGIndexResponse,
    RAGQueryRequest, RAGQueryResponse,
    RAGStatsResponse
)
from core.rag_engine import (
    create_vector_store, query_vector_store,
    delete_vector_store, list_vector_stores, get_store_stats
)
from utils.logger import log

router = APIRouter()


@router.post("/rag/index", response_model=RAGIndexResponse)
async def index_text(request: RAGIndexRequest):
    """
    Index text into a vector store for RAG querying.
    """
    log.info(f"RAG index endpoint: store_id={request.store_id}, text_length={len(request.text)}")
    
    try:
        store_id = create_vector_store(
            text=request.text,
            metadata=request.metadata,
            store_id=request.store_id
        )
        
        stats = get_store_stats(store_id)
        
        return RAGIndexResponse(
            success=True,
            message=f"Text indexed successfully in store '{store_id}'",
            store_id=store_id,
            num_chunks=stats["num_chunks"]
        )
    except Exception as e:
        log.error(f"RAG indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """
    Query a vector store with semantic search.
    """
    log.info(f"RAG query endpoint: store_id={request.store_id}, query={request.query}")
    
    try:
        result = query_vector_store(
            query=request.query,
            store_id=request.store_id,
            top_k=request.top_k
        )
        
        return RAGQueryResponse(
            success=True,
            query=request.query,
            chunks=result["chunks"],
            scores=result["scores"],
            metadata=result["metadata"]
        )
    except Exception as e:
        log.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/reset")
async def reset_store(store_id: str = "default"):
    """
    Delete a vector store.
    """
    log.info(f"RAG reset endpoint: store_id={store_id}")
    
    try:
        success = delete_vector_store(store_id)
        
        if success:
            return {"success": True, "message": f"Vector store '{store_id}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Vector store '{store_id}' not found")
    except Exception as e:
        log.error(f"RAG reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats", response_model=RAGStatsResponse)
async def get_stats(store_id: str = None):
    """
    Get statistics for vector stores.
    """
    log.info(f"RAG stats endpoint: store_id={store_id}")
    
    try:
        stores = list_vector_stores()
        
        if store_id:
            stats = get_store_stats(store_id)
            return RAGStatsResponse(
                success=True,
                stores=stores,
                stats=stats
            )
        else:
            return RAGStatsResponse(
                success=True,
                stores=stores
            )
    except Exception as e:
        log.error(f"RAG stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
