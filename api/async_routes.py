# api/async_routes.py
"""
Async API routes using Celery for background processing.
Provides endpoints for submitting async OCR jobs and checking status.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from pydantic import BaseModel
from core.celery_tasks import process_image_task, process_batch_task, index_document_task, generate_graph_task
from utils.logger import log

router = APIRouter()


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    result: dict = None
    error: str = None


class AsyncOCRResponse(BaseModel):
    """Response model for async OCR submission."""
    success: bool
    task_id: str
    message: str


@router.post("/async/ocr/image", response_model=AsyncOCRResponse)
async def async_ocr_image(file: UploadFile = File(...)):
    """
    Submit an image for async OCR processing.
    Returns a task ID to check status later.
    """
    try:
        content = await file.read()
        
        # Submit to Celery
        task = process_image_task.delay(content, file.filename)
        
        log.info(f"Submitted async OCR task {task.id} for {file.filename}")
        
        return AsyncOCRResponse(
            success=True,
            task_id=task.id,
            message=f"OCR task submitted for {file.filename}"
        )
    except Exception as e:
        log.error(f"Failed to submit async OCR task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/async/ocr/batch", response_model=AsyncOCRResponse)
async def async_ocr_batch(files: List[UploadFile] = File(...)):
    """
    Submit multiple files for batch async OCR processing.
    Returns a task ID to check status later.
    """
    try:
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append({
                "bytes": content,
                "filename": file.filename
            })
        
        # Submit to Celery
        task = process_batch_task.delay(files_data)
        
        log.info(f"Submitted batch OCR task {task.id} for {len(files)} files")
        
        return AsyncOCRResponse(
            success=True,
            task_id=task.id,
            message=f"Batch OCR task submitted for {len(files)} files"
        )
    except Exception as e:
        log.error(f"Failed to submit batch OCR task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/async/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an async task.
    """
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.state,
        }
        
        if task.state == 'PENDING':
            response["result"] = {"status": "Task is waiting to be processed"}
        elif task.state == 'PROCESSING':
            response["result"] = task.info
        elif task.state == 'SUCCESS':
            response["result"] = task.result
        elif task.state == 'FAILURE':
            response["error"] = str(task.info)
        
        return TaskStatusResponse(**response)
    except Exception as e:
        log.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/async/rag/index", response_model=AsyncOCRResponse)
async def async_rag_index(text: str, store_id: str = "default", metadata: dict = None):
    """
    Submit a document for async RAG indexing.
    """
    try:
        task = index_document_task.delay(text, store_id, metadata)
        
        log.info(f"Submitted async RAG indexing task {task.id}")
        
        return AsyncOCRResponse(
            success=True,
            task_id=task.id,
            message=f"RAG indexing task submitted for store '{store_id}'"
        )
    except Exception as e:
        log.error(f"Failed to submit RAG indexing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/async/kg/generate", response_model=AsyncOCRResponse)
async def async_kg_generate(fields: dict, doc_name: str = "Document", export_format: str = "json"):
    """
    Submit a knowledge graph generation task.
    """
    try:
        task = generate_graph_task.delay(fields, doc_name, export_format)
        
        log.info(f"Submitted async KG generation task {task.id}")
        
        return AsyncOCRResponse(
            success=True,
            task_id=task.id,
            message=f"Knowledge graph generation task submitted for '{doc_name}'"
        )
    except Exception as e:
        log.error(f"Failed to submit KG generation task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
