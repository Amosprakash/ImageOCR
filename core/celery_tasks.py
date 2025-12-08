# core/celery_tasks.py
"""
Celery tasks for asynchronous OCR processing.
Enables background processing of large documents and batch jobs.
"""
import os
from celery import Celery
from typing import Dict, Any
from utils.logger import log

# Initialize Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "imageai",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(bind=True, name="ocr.process_image")
def process_image_task(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Async task to process an image with OCR.
    
    Args:
        image_bytes: Raw image bytes
        filename: Original filename
        
    Returns:
        dict: OCR result with text and metadata
    """
    try:
        log.info(f"Starting OCR task for {filename}")
        self.update_state(state='PROCESSING', meta={'status': 'Extracting text...'})
        
        from utils.file_handler import extract_text_sync
        
        result = extract_text_sync(image_bytes, filename)
        
        log.info(f"OCR task completed for {filename}")
        return {
            "success": True,
            "filename": filename,
            "result": result
        }
    except Exception as e:
        log.error(f"OCR task failed for {filename}: {e}")
        return {
            "success": False,
            "filename": filename,
            "error": str(e)
        }


@celery_app.task(bind=True, name="ocr.process_batch")
def process_batch_task(self, files_data: list) -> Dict[str, Any]:
    """
    Async task to process multiple files in batch.
    
    Args:
        files_data: List of dicts with 'bytes' and 'filename'
        
    Returns:
        dict: Batch processing results
    """
    try:
        log.info(f"Starting batch OCR task for {len(files_data)} files")
        self.update_state(state='PROCESSING', meta={'status': f'Processing {len(files_data)} files...'})
        
        from utils.file_handler import extract_text_sync
        
        results = []
        for i, file_data in enumerate(files_data):
            self.update_state(
                state='PROCESSING',
                meta={'status': f'Processing file {i+1}/{len(files_data)}...'}
            )
            
            result = extract_text_sync(file_data['bytes'], file_data['filename'])
            results.append({
                "filename": file_data['filename'],
                "result": result
            })
        
        log.info(f"Batch OCR task completed for {len(files_data)} files")
        return {
            "success": True,
            "total_files": len(files_data),
            "results": results
        }
    except Exception as e:
        log.error(f"Batch OCR task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(bind=True, name="rag.index_document")
def index_document_task(self, text: str, store_id: str = "default", metadata: dict = None) -> Dict[str, Any]:
    """
    Async task to index a document into RAG vector store.
    
    Args:
        text: Document text to index
        store_id: Vector store identifier
        metadata: Optional metadata
        
    Returns:
        dict: Indexing result
    """
    try:
        log.info(f"Starting RAG indexing task for store '{store_id}'")
        self.update_state(state='PROCESSING', meta={'status': 'Creating embeddings...'})
        
        from core.rag_engine import create_vector_store, get_store_stats
        
        store_id = create_vector_store(text, metadata, store_id)
        stats = get_store_stats(store_id)
        
        log.info(f"RAG indexing task completed for store '{store_id}'")
        return {
            "success": True,
            "store_id": store_id,
            "stats": stats
        }
    except Exception as e:
        log.error(f"RAG indexing task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(bind=True, name="kg.generate_graph")
def generate_graph_task(self, fields: dict, doc_name: str = "Document", export_format: str = "json") -> Dict[str, Any]:
    """
    Async task to generate knowledge graph.
    
    Args:
        fields: Structured fields to convert to graph
        doc_name: Document name
        export_format: Export format (json, png, or both)
        
    Returns:
        dict: Graph generation result
    """
    try:
        log.info(f"Starting knowledge graph generation for '{doc_name}'")
        self.update_state(state='PROCESSING', meta={'status': 'Building graph...'})
        
        from core.kg_builder import build_graph_from_fields, export_graph_json, export_graph_png, get_graph_stats
        
        graph = build_graph_from_fields(fields, doc_name)
        stats = get_graph_stats(graph)
        
        output_paths = {}
        if export_format in ["json", "both"]:
            json_path = export_graph_json(graph)
            output_paths["json"] = json_path
        
        if export_format in ["png", "both"]:
            png_path = export_graph_png(graph)
            output_paths["png"] = png_path
        
        log.info(f"Knowledge graph generation completed for '{doc_name}'")
        return {
            "success": True,
            "doc_name": doc_name,
            "stats": stats,
            "output_paths": output_paths
        }
    except Exception as e:
        log.error(f"Knowledge graph generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
