# core/rag_engine.py
"""
RAG (Retrieval-Augmented Generation) engine for ImageAI.
Provides vector storage and semantic search over OCR-extracted documents.

Uses FAISS for vector storage and OpenAI embeddings for semantic search.
"""
import os
import json
import pickle
from typing import Dict, List, Optional, Any
from pathlib import Path
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not installed. Install with: pip install faiss-cpu")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from utils.logger import log

# Vector store directory
VECTOR_STORE_DIR = Path("models/vector_stores")
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Global store for active vector stores
_vector_stores: Dict[str, Dict[str, Any]] = {}


def create_vector_store(text: str, metadata: Optional[Dict] = None, store_id: str = "default") -> str:
    """
    Create or update a FAISS vector store from OCR text.

    Args:
        text: OCR extracted text to index
        metadata: Optional metadata to store with the text
        store_id: Unique identifier for this vector store

    Returns:
        str: Store ID
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS is not installed. Install with: pip install faiss-cpu")
    
    log.info(f"Creating vector store '{store_id}' with {len(text)} characters")
    
    # 1. Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    log.info(f"Split text into {len(chunks)} chunks")
    
    # 2. Create embeddings
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
    embeddings = embeddings_model.embed_documents(chunks)
    embeddings_array = np.array(embeddings).astype('float32')
    
    # 3. Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    # 4. Store chunks and metadata
    store_data = {
        "chunks": chunks,
        "metadata": metadata or {},
        "num_chunks": len(chunks),
        "total_chars": len(text),
        "embedding_model": "text-embedding-3-small"
    }
    
    # 5. Save to disk
    store_path = VECTOR_STORE_DIR / store_id
    store_path.mkdir(exist_ok=True)
    
    faiss.write_index(index, str(store_path / "index.faiss"))
    with open(store_path / "data.pkl", "wb") as f:
        pickle.dump(store_data, f)
    with open(store_path / "metadata.json", "w") as f:
        json.dump(store_data["metadata"], f, indent=2)
    
    # 6. Cache in memory
    _vector_stores[store_id] = {
        "index": index,
        "data": store_data,
        "embeddings_model": embeddings_model
    }
    
    log.info(f"Vector store '{store_id}' created successfully with {len(chunks)} chunks")
    return store_id


def query_vector_store(query: str, store_id: str = "default", top_k: int = 5) -> Dict[str, Any]:
    """
    Query a vector store with semantic search.

    Args:
        query: Search query
        store_id: Vector store identifier
        top_k: Number of top results to return

    Returns:
        dict: {
            "chunks": List[str],
            "scores": List[float],
            "metadata": dict
        }
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS is not installed. Install with: pip install faiss-cpu")
    
    log.info(f"Querying vector store '{store_id}' with: {query}")
    
    # 1. Load store if not in memory
    if store_id not in _vector_stores:
        _load_vector_store(store_id)
    
    if store_id not in _vector_stores:
        raise ValueError(f"Vector store '{store_id}' not found")
    
    store = _vector_stores[store_id]
    index = store["index"]
    data = store["data"]
    embeddings_model = store["embeddings_model"]
    
    # 2. Embed query
    query_embedding = embeddings_model.embed_query(query)
    query_array = np.array([query_embedding]).astype('float32')
    
    # 3. Search
    distances, indices = index.search(query_array, min(top_k, len(data["chunks"])))
    
    # 4. Get results
    results = []
    scores = []
    for i, idx in enumerate(indices[0]):
        if idx < len(data["chunks"]):
            results.append(data["chunks"][idx])
            # Convert L2 distance to similarity score (inverse)
            scores.append(float(1 / (1 + distances[0][i])))
    
    log.info(f"Found {len(results)} relevant chunks")
    
    return {
        "chunks": results,
        "scores": scores,
        "metadata": data["metadata"]
    }


def delete_vector_store(store_id: str = "default") -> bool:
    """
    Delete a vector store.

    Args:
        store_id: Vector store identifier

    Returns:
        bool: True if deleted successfully
    """
    log.info(f"Deleting vector store '{store_id}'")
    
    # Remove from memory
    if store_id in _vector_stores:
        del _vector_stores[store_id]
    
    # Remove from disk
    store_path = VECTOR_STORE_DIR / store_id
    if store_path.exists():
        import shutil
        shutil.rmtree(store_path)
        log.info(f"Vector store '{store_id}' deleted successfully")
        return True
    
    log.warning(f"Vector store '{store_id}' not found")
    return False


def list_vector_stores() -> List[str]:
    """
    List all available vector stores.

    Returns:
        List[str]: List of store IDs
    """
    stores = [d.name for d in VECTOR_STORE_DIR.iterdir() if d.is_dir()]
    log.info(f"Found {len(stores)} vector stores")
    return stores


def get_store_stats(store_id: str = "default") -> Dict[str, Any]:
    """
    Get statistics for a vector store.

    Args:
        store_id: Vector store identifier

    Returns:
        dict: Statistics including num_chunks, total_chars, etc.
    """
    # Load store if not in memory
    if store_id not in _vector_stores:
        _load_vector_store(store_id)
    
    if store_id not in _vector_stores:
        raise ValueError(f"Vector store '{store_id}' not found")
    
    data = _vector_stores[store_id]["data"]
    
    return {
        "store_id": store_id,
        "num_chunks": data["num_chunks"],
        "total_chars": data["total_chars"],
        "embedding_model": data["embedding_model"],
        "metadata": data["metadata"]
    }


def _load_vector_store(store_id: str):
    """
    Load a vector store from disk into memory.

    Args:
        store_id: Vector store identifier
    """
    store_path = VECTOR_STORE_DIR / store_id
    
    if not store_path.exists():
        log.warning(f"Vector store '{store_id}' not found on disk")
        return
    
    # Load index
    index = faiss.read_index(str(store_path / "index.faiss"))
    
    # Load data
    with open(store_path / "data.pkl", "rb") as f:
        data = pickle.load(f)
    
    # Create embeddings model
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Cache in memory
    _vector_stores[store_id] = {
        "index": index,
        "data": data,
        "embeddings_model": embeddings_model
    }
    
    log.info(f"Loaded vector store '{store_id}' from disk")
